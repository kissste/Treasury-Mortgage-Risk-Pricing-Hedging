from QuantLib.QuantLib import HestonSLVFDMModel, IborIndex, Schedule
import QuantLib as ql
import numpy as np
import pandas as pd
from datetime import date

from pandas.core import base

def prep_curve(calculation_date, rates):
    # create piecewise yield term structure
    class PiecewiseCurveBuilder:
        def __init__(self, settlementDate, dayCounter):
            self.helpers = []
            self.settlementDate = settlementDate
            self.dayCounter = dayCounter

        # 4th constructor: DepositRateHelper(Rate rate, const shared_ptr<IborIndex> &iborIndex)
        def AddDeposit(self, rate, iborIndex):
            helper = ql.DepositRateHelper(rate, iborIndex)
            self.helpers.append(helper)

        # 4th constructor: FraRateHelper(Rate rate, Natural monthsToStart, const shared_ptr<IborIndex> &iborIndex)
        def AddFRA(self, rate, monthsToStart, iborIndex):
            helper = ql.FraRateHelper(rate, monthsToStart, iborIndex)
            self.helpers.append(helper)
        
        # 6th constructor (Real price, const Date &iborStartDate, const ext::shared_ptr<IborIndex> &iborIndex) 
        def AddFuture(self, price, iborStartDate, iborIndex):
            helper = ql.FuturesRateHelper(price, iborStartDate, iborIndex)
            self.helpers.append(helper)
        
        # 4th constructor: SwapRateHelper(Rate rate, const Period &tenor, const Calendar &calendar, 
        # Frequency fixedFrequency, BusinessDayConvention fixedConvention, const DayCounter &fixedDayCount, 
        # const shared_ptr<IborIndex> &iborIndex)
        def AddSwap(self, rate, periodLength, fixedCalendar, fixedFrequency, fixedConvention, fixedDayCount, floatIndex):
            helper = ql.SwapRateHelper(rate, periodLength, fixedCalendar, fixedFrequency, 
                fixedConvention, fixedDayCount, floatIndex)
            self.helpers.append(helper)
        
        # PiecewiseYieldCurve <ZeroYield, Linear>
        def GetCurveHandle(self):  
            yieldTermStructure = ql.PiecewiseLinearZero(self.settlementDate, self.helpers, self.dayCounter)
            return ql.RelinkableYieldTermStructureHandle(yieldTermStructure)


    # general parameters    
    tradeDate = calculation_date #ql.Date(4, ql.February, 2020)
    calendar = ql.TARGET()
    dayCounter = ql.Actual360()
    convention = ql.ModifiedFollowing
    settlementDate = calendar.advance(tradeDate, ql.Period(2, ql.Days), convention)  
    swapIndex = ql.USDLibor(ql.Period(3, ql.Months))
    frequency = ql.Semiannual

    # create curve builder object
    ql.Settings.instance().evaluationDate = tradeDate
    builder = PiecewiseCurveBuilder(settlementDate, dayCounter)

    # cash deposit
    depos = []
    #depos.append((0.032175, ql.USDLibor(ql.Period(1, ql.Weeks))))
    #depos.append((0.0318125, ql.USDLibor(ql.Period(1, ql.Months))))
    #depos.append((0.03145, ql.USDLibor(ql.Period(3, ql.Months))))
    [builder.AddDeposit(d[2], d[3]) 
        for d in filter(lambda x: x[1]=='Deposit', rates)]

    # futures
    futures = []
    #futures.append((97.41, ql.IMM.nextDate(settlementDate + ql.Period(3, ql.Months)), swapIndex))
    #futures.append((97.52, ql.IMM.nextDate(settlementDate + ql.Period(6, ql.Months)), swapIndex))
    #futures.append((97.495, ql.IMM.nextDate(settlementDate + ql.Period(9, ql.Months)), swapIndex))
    #futures.append((97.395, ql.IMM.nextDate(settlementDate + ql.Period(12, ql.Months)), swapIndex))
    #futures.append((97.395, ql.IMM.nextDate(settlementDate + ql.Period(15, ql.Months)), swapIndex))
    #futures.append((97.395, ql.IMM.nextDate(settlementDate + ql.Period(18, ql.Months)), swapIndex))
    [builder.AddFuture(f[2], f[3], f[4]) 
        for f in filter(lambda x: x[1]=='Future', rates)]

    # swaps
    swaps = []
    #swaps.append((0.02795, ql.Period(2, ql.Years), calendar, frequency, convention, dayCounter, swapIndex))
    #swaps.append((0.03035, ql.Period(3, ql.Years), calendar, frequency, convention, dayCounter, swapIndex))
    #swaps.append((0.03275, ql.Period(4, ql.Years), calendar, frequency, convention, dayCounter, swapIndex))
    #swaps.append((0.03505, ql.Period(5, ql.Years), calendar, frequency, convention, dayCounter, swapIndex))
    #swaps.append((0.03715, ql.Period(6, ql.Years), calendar, frequency, convention, dayCounter, swapIndex))
    #swaps.append((0.03885, ql.Period(7, ql.Years), calendar, frequency, convention, dayCounter, swapIndex))
    #swaps.append((0.04025, ql.Period(8, ql.Years), calendar, frequency, convention, dayCounter, swapIndex))
    #swaps.append((0.04155, ql.Period(9, ql.Years), calendar, frequency, convention, dayCounter, swapIndex))
    #swaps.append((0.04265, ql.Period(10, ql.Years), calendar, frequency, convention, dayCounter, swapIndex))
    #swaps.append((0.04435, ql.Period(12, ql.Years), calendar, frequency, convention, dayCounter, swapIndex))
    [builder.AddSwap(s[2], s[3], s[4], s[5], s[6], s[7], s[8]) 
        for s in filter(lambda x: x[1]=='Swap', rates)]

    # get relinkable curve handle from builder
    curve = builder.GetCurveHandle()
    curve.enableExtrapolation()

    # create and print array of discount factors for every 3M up to 15Y
    #times = np.linspace(0.0, 15.0, 61)
    #dfs = np.array([curve.discount(t) for t in times])
    #print(dfs)
    return curve

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
    #yts = ql.YieldTermStructureHandle(ql.FlatForward(2, ql.TARGET(), 0.5, ql.Actual360()))

    #yts = forecast_yield = prep_curve(calculation_date)

    fytsBase = curves[0]
    ytsBase = curves[0]

    iborIndexBase = ql.Libor('MyIndex', ql.Period('1M'), 2, ql.USDCurrency(), ql.TARGET(), ql.Actual360()
        , fytsBase)
    iborIndexBase.addFixing(ql.Date(2,7,2021), 0.01)

    tp = 0.0150 #starting point
    fixedLeg = ql.FixedRateLeg(schedulerBase, ql.Actual360(), notionals, [tp])
    floatLeg = ql.IborLeg(notionals, schedulerBase, iborIndexBase, ql.Actual360(), ql.ModifiedFollowing, fixingDays=[2])
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
    fixedLeg1 = ql.FixedRateLeg(schedulerBase, ql.Actual360(), notionals, [tp1])
    swap1 = ql.Swap(fixedLeg1, floatLeg)
    swap1.setPricingEngine(engineBase)
    s1 = swap1.NPV()
    #print('s1:',tp1, s1)

    tp2 = tp + s/(s-s1)*(tp1-tp)

    fixedLeg2 = ql.FixedRateLeg(schedulerBase, ql.Actual360(), notionals, [tp2])
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
    baseNPV = s2

    #Calculate Risk 
    fixedLeg = ql.FixedRateLeg(schedulerBase, ql.Actual360(), notionals, [tp])
    for i in range(len(curves)-1,-1,-1):
        fyts = curves[i]
        yts = curves[i]
        
        iborIndex = ql.Libor('MyIndex', ql.Period('1M'), 2, ql.USDCurrency(), ql.TARGET(), ql.Actual360(), fyts)
        iborIndex.addFixing(ql.Date(2,7,2021), 0.01)
        floatLeg = ql.IborLeg(notionals, schedulerBase, iborIndex, ql.Actual360(), ql.ModifiedFollowing, fixingDays=[2])
        swap = ql.Swap(fixedLeg, floatLeg)
        engine = ql.DiscountingSwapEngine(yts)
        swap.setPricingEngine(engine)
        s1 = swap.NPV()
        if i == 0: 
            baseNPV = s1
            reportNPV = s1
        else:
            reportNPV = s1 - baseNPV            
        label = rates[i-1][0] if i > 0 else 'Base'
        print('sx:', i, label, reportNPV)

        notionalsFlat = [1]
        rateHedge = rates[i-1][2]
        print(rates[i-1][3])
        s = rates[i-1]

        helper = ql.SwapRateHelper(s[2], s[3], s[4], s[5], s[6], s[7], s[8])
        matDate = helper.maturityDate()
        print(matDate)

        scheduler = ql.MakeSchedule(start_date, matDate, ql.Period('1m'), rule=ql.DateGeneration.Backward, convention=ql.ModifiedFollowing, calendar=ql.UnitedStates(ql.UnitedStates.Settlement))


        fixedLegHedge = ql.FixedRateLeg(scheduler, ql.Actual360(), notionalsFlat, [rateHedge])
        floatLegHedge = ql.IborLeg(notionalsFlat, scheduler, iborIndex, ql.Actual360(), ql.ModifiedFollowing, fixingDays=[2])        
        swapHedge = ql.Swap(fixedLegHedge, floatLegHedge)
        engine = ql.DiscountingSwapEngine(yts)
        swapHedge.setPricingEngine(engine)
        s1 = swapHedge.NPV()        
        hedgeNotional = reportNPV/s1
        print('Bumped', rateHedge, s1, hedgeNotional)

        iborIndexBase = ql.Libor('MyIndex', ql.Period('1M'), 2, ql.USDCurrency(), ql.TARGET(), ql.Actual360()
            , fytsBase)
        iborIndexBase.addFixing(ql.Date(2,7,2021), 0.01)
        fixedLegHedgeBase = ql.FixedRateLeg(scheduler, ql.Actual360(), notionalsFlat, [rateHedge])
        floatLegHedgeBase = ql.IborLeg(notionalsFlat, scheduler, iborIndexBase, ql.Actual360(), ql.ModifiedFollowing, fixingDays=[2])        
        swapHedgeBase = ql.Swap(fixedLegHedgeBase, floatLegHedgeBase)
        engineBase = ql.DiscountingSwapEngine(ytsBase)
        swapHedgeBase.setPricingEngine(engineBase)
        s1Base = swapHedgeBase.NPV()        
        print('Base  ', rateHedge, s1Base, hedgeNotional)


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
convention = ql.ModifiedFollowing
settlementDate = calendar.advance(tradeDate, ql.Period(2, ql.Days), convention)  
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
    ('SWAP  2Y', 'Swap', 0.02795, ql.Period(2, ql.Years), calendar, frequency, convention, dayCounter, swapIndex),
    ('SWAP  3Y', 'Swap', 0.03035, ql.Period(3, ql.Years), calendar, frequency, convention, dayCounter, swapIndex),
    ('SWAP  4Y', 'Swap', 0.03275, ql.Period(4, ql.Years), calendar, frequency, convention, dayCounter, swapIndex),
    ('SWAP  5Y', 'Swap', 0.03505, ql.Period(5, ql.Years), calendar, frequency, convention, dayCounter, swapIndex),
    ('SWAP  6Y', 'Swap', 0.03715, ql.Period(6, ql.Years), calendar, frequency, convention, dayCounter, swapIndex),
    ('SWAP  7Y', 'Swap', 0.03885, ql.Period(7, ql.Years), calendar, frequency, convention, dayCounter, swapIndex),
    ('SWAP  8Y', 'Swap', 0.04025, ql.Period(8, ql.Years), calendar, frequency, convention, dayCounter, swapIndex),
    ('SWAP  9Y', 'Swap', 0.04155, ql.Period(9, ql.Years), calendar, frequency, convention, dayCounter, swapIndex),
    ('SWAP 10Y', 'Swap', 0.04265, ql.Period(10, ql.Years), calendar, frequency, convention, dayCounter, swapIndex),
    ('SWAP 12Y', 'Swap', 0.04435, ql.Period(12, ql.Years), calendar, frequency, convention, dayCounter, swapIndex),
]

curves = []
curves.append(prep_curve(calculation_date, rates))

for i in range(0, len(rates), 1):
    #print(i)
    ratescopy = rates[:]
    bump = 0.01 if (ratescopy[i][1] == 'Future') else 0.01/100
    ratescopyL = list(ratescopy[i])
    ratescopyL[2] = ratescopyL[2] + bump
    ratescopy[i] = tuple(ratescopyL)
    #print(ratescopy)
    curves.append(prep_curve(calculation_date, ratescopy))

value_mortgage(mortgage, calc_date, curves, rates)
print(calc_date)

#start = ql.Date(7,5,2020)
#end = ql.Date(31,8,2020)

#schedule2 = ql.MakeSchedule(start, end, ql.Period('1m'), rule=ql.DateGeneration.Backward, convention=ql.ModifiedFollowing, calendar=ql.UnitedStates(ql.UnitedStates.Settlement))
#print([dt for dt in schedule2])