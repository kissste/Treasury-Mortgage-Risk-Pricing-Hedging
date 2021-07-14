from QuantLib.QuantLib import HestonSLVFDMModel, IborIndex, Schedule
import QuantLib as ql
import numpy as np
import pandas as pd
from datetime import date
from pandas.core import base

def bootstrap_curves(calculation_date, rates):
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
    conventionMD = ql.ModifiedFollowing
    settlementDate = calendar.advance(tradeDate, ql.Period(2, ql.Days), conventionMD)  
    #swapIndex = ql.USDLibor(ql.Period(3, ql.Months))
    #frequency = ql.Annual

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