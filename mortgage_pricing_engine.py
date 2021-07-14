from QuantLib.QuantLib import ForwardRateAgreement, Futures, HestonSLVFDMModel, IborIndex, Schedule
import QuantLib as ql
import numpy as np
import pandas as pd
from datetime import date
from mortgage_pricing_engine_bootstrapping import *
from mortgage_pricing_engine_ontherun import *
from pandas.core import base

def value_mortgage(mortgage, calc_date, curves, rates):
    calculation_date = ql.Date(calc_date.day, calc_date.month, calc_date.year)
    ql.Settings.instance().evaluationDate = calculation_date

    # conventions
    day_count = ql.Actual360()
    calendar = ql.UnitedStates()
    dividend_rate = 0.0163

    maturity = mortgage["Maturity"]
    lqr = mortgage["LQR"]/12.0
    ppr = mortgage["PPR"]/12.0
    coupon = mortgage["Coupon"]/12.0
    paymentMonthly = mortgage["PaymentMonthly"]
    principalAmount = mortgage["PrincipalAmount"]

    maturity_date = ql.Date(maturity,"%Y-%m-%d")
    start_date = calculation_date
    schedulerBase = ql.MakeSchedule(start_date, maturity_date, ql.Period('1m'), rule=ql.DateGeneration.Backward, convention=ql.ModifiedFollowing, calendar=ql.UnitedStates(ql.UnitedStates.Settlement))
    #print([dt for dt in schedule])
    #print(len(scheduler))

    notionals = [principalAmount]
    schedule = [schedulerBase[0]]
    index = 0

    while (principalAmount > 0.0):
        interest = round(principalAmount * coupon,2)
        scheduledPrincipalPayment = paymentMonthly - interest
        if(scheduledPrincipalPayment < 0.0): break

        remainingPrincipalAmount = principalAmount - scheduledPrincipalPayment
        if(remainingPrincipalAmount < 0.0): 
            remainingPrincipalAmount = 0.0
            scheduledPrincipalPayment = principalAmount

        prepayPayment = round(remainingPrincipalAmount * ppr,2)
        remainingPrincipalAmount = remainingPrincipalAmount - prepayPayment
        if(remainingPrincipalAmount < 0.0): 
            remainingPrincipalAmount = 0.0
            prepayPayment = remainingPrincipalAmount

        liquidationPayment = round(remainingPrincipalAmount * lqr,2)
        principalAmount = remainingPrincipalAmount - liquidationPayment
        if(remainingPrincipalAmount < 0.0): 
            remainingPrincipalAmount = 0.0
            liquidationPayment = remainingPrincipalAmount

        #print(principalAmount)
        if(index + 2 >= len(schedulerBase)): break
        index += 1 
        #print(index)
        notionals.append(principalAmount)
        schedule.append(schedulerBase[index])

    #print([dt for dt in notionals])
    #print([dt for dt in schedule])

    #forecast_yield = ql.YieldTermStructureHandle(ql.FlatForward(calculation_date, dividend_rate, day_count))
    #yts = ql.YieldTermStructureHandle(ql.FlatForward(2, ql.TARGET(), 0.5, dayCounter))

    #yts = forecast_yield = prep_curve(calculation_date)

    fytsBase = curves[0]
    ytsBase = curves[0]

    iborIndexBase = ql.Libor('SK1MBase', ql.Period('1M'), 2, ql.USDCurrency(), ql.TARGET(), dayCounter
        , fytsBase)
    iborIndexBase.addFixing(ql.Date(2,7,2021), 0.01)

    tp = 0.0150 #starting point
    fixedLeg = ql.FixedRateLeg(schedulerBase, dayCounter, notionals, [tp])
    floatLeg = ql.IborLeg(notionals, schedulerBase, iborIndexBase, dayCounter, conventionMD, fixingDays=[2])
    swap = ql.Swap(fixedLeg, floatLeg)

    #l1 = ql.CashFlows.npv(fixedLeg, yts, True)
    #print(l1)

    engineBase = ql.DiscountingSwapEngine(ytsBase)
    swap.setPricingEngine(engineBase)

    #fixingDates = [cf.fixingDate() for cf in map(ql.as_floating_rate_coupon, floatLeg.floatingLeg())]
    #print(fixingDates)

    #swap.fairRate()
    s = swap.NPV()
    #print('s:', tp, s)
    #l1 = swap.legNPV(0)
    #print(l1)
    #l2 = swap.legNPV(1)
    #print(l2)

    tp1 = tp + 1.0/10000.0
    fixedLeg1 = ql.FixedRateLeg(schedulerBase, dayCounter, notionals, [tp1])
    swap1 = ql.Swap(fixedLeg1, floatLeg)
    swap1.setPricingEngine(engineBase)
    s1Hedge = swap1.NPV()
    #print('s1:',tp1, s1)

    tp2 = tp + s/(s-s1Hedge)*(tp1-tp)

    fixedLeg2 = ql.FixedRateLeg(schedulerBase, dayCounter, notionals, [tp2])
    swap2 = ql.Swap(fixedLeg2, floatLeg)
    swap2.setPricingEngine(engineBase)
    s2 = swap2.NPV()
    print('s2:', tp2, s2)

    #l1 = swap2.legNPV(0)
    #print(l1)
    #l2 = swap2.legNPV(1)
    #print(l2)

    #print(swap.legBPS(0))

    tp = tp2
    baseMtgNPV = s2

    #Calculate Risk 
    fixedLeg = ql.FixedRateLeg(schedulerBase, dayCounter, notionals, [tp])
    for i in range(len(curves)-1,-1,-1):
        fyts = curves[i]
        yts = curves[i]
        
        iborIndex = ql.Libor('SK1M', ql.Period('1M'), 2, ql.USDCurrency(), ql.TARGET(), dayCounter, fyts)
        iborIndex.addFixing(ql.Date(2,7,2021), 0.01)
        floatLeg = ql.IborLeg(notionals, schedulerBase, iborIndex, dayCounter, conventionMD, fixingDays=[2])
        swap = ql.Swap(fixedLeg, floatLeg)
        engine = ql.DiscountingSwapEngine(yts)
        swap.setPricingEngine(engine)
        s1Mtg = swap.NPV()
        if i == 0: 
            baseMtgNPV = s1Mtg
            deltaMtg = s1Mtg
            continue
        else:
            deltaMtg = s1Mtg - baseMtgNPV
        s = rates[i-1]                     
        label = s[0] if i > 0 else 'Base'
        print('sx:', i, label, 'DeltaMtg:', deltaMtg)

        notionalsFlat = [1]
        instrumentType = s[1]
        rateHedge = s[2]
        maturity = s[3]

        if instrumentType == 'Swap':
            helper = ql.SwapRateHelper(s[2], s[3], s[4], s[5], s[6], s[7], s[8])
            matDate = helper.maturityDate()
            #print(maturity, rateHedge, matDate)

            deltaHedge = onTheRunSwapDelta(start_date, matDate, rateHedge, fytsBase, ytsBase, fyts, yts)            
            hedgeNotional = deltaMtg / deltaHedge
            
            print('HedgeNotional:', hedgeNotional)

        elif instrumentType == 'Future':
            deltaHedge = onTheRunFutureDelta(maturity, rateHedge, fytsBase, ytsBase, fyts, yts)

            hedgeNotional = deltaMtg/deltaHedge

            print('HedgeNotional:', hedgeNotional)

        elif instrumentType == 'Deposit':
            helper = ql.DepositRateHelper(rateHedge, maturity)
            matDate = helper.maturityDate()
            #print(matDate)

            deltaHedge = onTheRunDepositDelta(settlementDate, matDate, rateHedge, ytsBase, yts)

            if deltaHedge!=0:
                hedgeNotional = deltaMtg/deltaHedge
                print('HedgeNotional:', hedgeNotional)


mortgage = {
    "AsOfDate": "2021-07-05",
    "TradeId": "New_Trd_Test",
    "Ticker": "OXY",
    "Book": "EQ_VOL_HED",
    "Product": "EQ_Option",
    "Quantity": 45,
    "Strike": -31.41249430583221,
    "Maturity": "2026-10-05",
    "LQR": 0.07,
    "PPR": 0.05,
    "Coupon": 0.0259,
    "PaymentMonthly": 5000,
    "PrincipalAmount": 1000000,
    "OptionType": "put",
    "MarketValue": 89.43425919208067
}

calc_date = date(2021, 7, 5)
calculation_date = ql.Date(calc_date.day, calc_date.month, calc_date.year)
ql.Settings.instance().evaluationDate = calculation_date

tradeDate = calculation_date #ql.Date(4, ql.February, 2020)
calendar = ql.TARGET()
dayCounter = ql.Actual360()
conventionMD = ql.ModifiedFollowing
settlementDate = calendar.advance(tradeDate, ql.Period(2, ql.Days), conventionMD)  
swapIndex = ql.USDLibor(ql.Period(3, ql.Months))
frequency = ql.Annual

rates = [
    ('MM 1W', 'Deposit', 0.032175, ql.USDLibor(ql.Period(1, ql.Weeks))),
    ('MM 1M', 'Deposit', 0.0318125, ql.USDLibor(ql.Period(1, ql.Months))),
    ('MM 3M', 'Deposit', 0.03145, ql.USDLibor(ql.Period(3, ql.Months))),
    ('FUT 1', 'Future', 97.41, ql.IMM.nextDate(settlementDate + ql.Period(3, ql.Months)), swapIndex),
    ('FUT 2', 'Future', 97.52, ql.IMM.nextDate(settlementDate + ql.Period(6, ql.Months)), swapIndex),
    ('FUT 3', 'Future', 97.495, ql.IMM.nextDate(settlementDate + ql.Period(9, ql.Months)), swapIndex),
    ('FUT 4', 'Future', 97.395, ql.IMM.nextDate(settlementDate + ql.Period(12, ql.Months)), swapIndex),
    ('FUT 5', 'Future', 97.395, ql.IMM.nextDate(settlementDate + ql.Period(15, ql.Months)), swapIndex),
    ('FUT 6', 'Future', 97.395, ql.IMM.nextDate(settlementDate + ql.Period(18, ql.Months)), swapIndex),
    ('SWAP  2Y', 'Swap', 0.02795, ql.Period(2, ql.Years), calendar, frequency, conventionMD, dayCounter, swapIndex),
    ('SWAP  3Y', 'Swap', 0.03035, ql.Period(3, ql.Years), calendar, frequency, conventionMD, dayCounter, swapIndex),
    ('SWAP  4Y', 'Swap', 0.03275, ql.Period(4, ql.Years), calendar, frequency, conventionMD, dayCounter, swapIndex),
    ('SWAP  5Y', 'Swap', 0.03505, ql.Period(5, ql.Years), calendar, frequency, conventionMD, dayCounter, swapIndex),
    ('SWAP  6Y', 'Swap', 0.03715, ql.Period(6, ql.Years), calendar, frequency, conventionMD, dayCounter, swapIndex),
    ('SWAP  7Y', 'Swap', 0.03885, ql.Period(7, ql.Years), calendar, frequency, conventionMD, dayCounter, swapIndex),
    ('SWAP  8Y', 'Swap', 0.04025, ql.Period(8, ql.Years), calendar, frequency, conventionMD, dayCounter, swapIndex),
    ('SWAP  9Y', 'Swap', 0.04155, ql.Period(9, ql.Years), calendar, frequency, conventionMD, dayCounter, swapIndex),
    ('SWAP 10Y', 'Swap', 0.04265, ql.Period(10, ql.Years), calendar, frequency, conventionMD, dayCounter, swapIndex),
    ('SWAP 12Y', 'Swap', 0.04435, ql.Period(12, ql.Years), calendar, frequency, conventionMD, dayCounter, swapIndex),
]

curves = []
curves.append(bootstrap_curves(calculation_date, rates))

for i in range(0, len(rates), 1):
    #print(i)
    ratescopy = rates[:]
    bump = 0.01 if (ratescopy[i][1] == 'Future') else 0.01/100
    ratescopyL = list(ratescopy[i])
    ratescopyL[2] = ratescopyL[2] + bump
    ratescopy[i] = tuple(ratescopyL)
    #print(ratescopy)
    curves.append(bootstrap_curves(calculation_date, ratescopy))

value_mortgage(mortgage, calc_date, curves, rates)
print(calc_date)

#start = ql.Date(7,5,2020)
#end = ql.Date(31,8,2020)

#schedule2 = ql.MakeSchedule(start, end, ql.Period('1m'), rule=ql.DateGeneration.Backward, convention=ql.ModifiedFollowing, calendar=ql.UnitedStates(ql.UnitedStates.Settlement))
#print([dt for dt in schedule2])