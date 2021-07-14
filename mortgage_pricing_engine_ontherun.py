from QuantLib.QuantLib import HestonSLVFDMModel, IborIndex, Schedule
import QuantLib as ql
import numpy as np
import pandas as pd
from datetime import date
from pandas.core import base

def onTheRunSwapNPV(start_date, matDate, rateHedge, fytsBase, ytsBase):
    calendar = ql.TARGET()
    dayCounter = ql.Actual360()
    conventionMD = ql.ModifiedFollowing

    notionalsFlat = [1]

    scheduler = ql.MakeSchedule(start_date, matDate, ql.Period('3m'), rule=ql.DateGeneration.Backward
        , convention=conventionMD, calendar=ql.UnitedStates(ql.UnitedStates.Settlement))

    iborIndexBase = ql.Libor('SK3MBase', ql.Period('3m'), 2, ql.USDCurrency(), ql.TARGET(), dayCounter
        , fytsBase)
    iborIndexBase.addFixing(ql.Date(2,7,2021), 0.01)
    fixedLegHedgeBase = ql.FixedRateLeg(scheduler, dayCounter, notionalsFlat, [rateHedge])
    floatLegHedgeBase = ql.IborLeg(notionalsFlat, scheduler, iborIndexBase, dayCounter, conventionMD, fixingDays=[2])        
    swapHedgeBase = ql.Swap(fixedLegHedgeBase, floatLegHedgeBase)
    engineBase = ql.DiscountingSwapEngine(ytsBase)
    swapHedgeBase.setPricingEngine(engineBase)
    s1HedgeBase = swapHedgeBase.NPV()

    return s1HedgeBase

    
def onTheRunSwapDelta(start_date, matDate, rateHedge, fytsBase, ytsBase, fyts, yts):
    s1HedgeBase = onTheRunSwapNPV(start_date, matDate, rateHedge, fytsBase, ytsBase)
    s1Hedge = onTheRunSwapNPV(start_date, matDate, rateHedge, fyts, yts)  

    return s1HedgeBase - s1Hedge


def onTheRunFutureNPV(maturity, rateHedge, fytsBase, ytsBase):
    fraBase = ql.ForwardRateAgreement(maturity, maturity + ql.Period(3, ql.Months)
        , ql.Position.Long, (100-rateHedge)/100, 1e6, ql.USDLibor(ql.Period(3, ql.Months), fytsBase), ytsBase)            
    fraNPVBase = fraBase.NPV()

    return fraNPVBase


def onTheRunFutureDelta(maturity, rateHedge, fytsBase, ytsBase, fyts, yts):
    fraHedgeBase = onTheRunFutureNPV(maturity, rateHedge, fytsBase, ytsBase)
    fraHedge = onTheRunFutureNPV(maturity, rateHedge, fyts, yts)  

    return fraHedgeBase - fraHedge


def onTheRunDepositNPV(settlementDate, matDate, rateHedge, ytsBase):
    depositBase = ql.FixedRateBond(2, ql.TARGET(), 1, settlementDate, matDate, ql.Period('1Y'), [rateHedge], ql.Actual360())
    engineBase = ql.DiscountingBondEngine(ytsBase)
    depositBase.setPricingEngine(engineBase)
    depositNPVBase = depositBase.NPV()

    return depositNPVBase


def onTheRunDepositDelta(settlementDate, matDate, rateHedge, ytsBase, yts):
    depositHedgeBase = onTheRunDepositNPV(settlementDate, matDate, rateHedge, ytsBase)
    depositHedge = onTheRunDepositNPV(settlementDate, matDate, rateHedge, yts)

    return depositHedgeBase - depositHedge    