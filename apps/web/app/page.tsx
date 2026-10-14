"use client";

import React, { useState, useEffect, useCallback } from "react";
import { Sidebar, NavTab } from "@/components/Sidebar";
import { Header } from "@/components/Header";
import { PaperTradingBanner } from "@/components/PaperTradingBanner";
import { KillSwitchModal } from "@/components/KillSwitchModal";
import { OverviewView } from "@/features/OverviewView";
import { PortfolioView } from "@/features/PortfolioView";
import { PositionsView } from "@/features/PositionsView";
import { OrdersView } from "@/features/OrdersView";
import { StrategiesView } from "@/features/StrategiesView";
import { ResearchLabView } from "@/features/ResearchLabView";
import { BacktestsView } from "@/features/BacktestsView";
import { RiskCenterView } from "@/features/RiskCenterView";
import { MarketRegimeView } from "@/features/MarketRegimeView";
import { TradeExplainView } from "@/features/TradeExplainView";
import { SystemHealthView } from "@/features/SystemHealthView";
import { AuditLogView } from "@/features/AuditLogView";
import { api } from "@/lib/api";

export default function DashboardPage() {
  const [currentTab, setCurrentTab] = useState<NavTab>("overview");
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [isKillModalOpen, setIsKillModalOpen] = useState(false);

  // Core state
  const [portfolio, setPortfolio] = useState<any>(null);
  const [history, setHistory] = useState<any[]>([]);
  const [positions, setPositions] = useState<any[]>([]);
  const [orders, setOrders] = useState<any[]>([]);
  const [strategies, setStrategies] = useState<any[]>([]);
  const [backtests, setBacktests] = useState<any[]>([]);
  const [researchData, setResearchData] = useState<any>(null);
  const [riskData, setRiskData] = useState<any>(null);
  const [regimeData, setRegimeData] = useState<any>(null);
  const [auditLogs, setAuditLogs] = useState<any[]>([]);

  const loadData = useCallback(async () => {
    setIsRefreshing(true);
    try {
      const [
        portRes,
        histRes,
        posRes,
        ordRes,
        stratRes,
        btRes,
        resRes,
        riskRes,
        regRes,
        audRes,
      ] = await Promise.allSettled([
        api.getPortfolio(),
        api.getPortfolioHistory(),
        api.getPositions("all"),
        api.getOrders(),
        api.getStrategies(),
        api.getBacktests(),
        api.getResearch(),
        api.getRiskStatus(),
        api.getRegime(),
        api.getAuditTrail(50),
      ]);

      if (portRes.status === "fulfilled") setPortfolio(portRes.value);
      if (histRes.status === "fulfilled") setHistory(histRes.value);
      if (posRes.status === "fulfilled") setPositions(posRes.value);
      if (ordRes.status === "fulfilled") setOrders(ordRes.value);
      if (stratRes.status === "fulfilled") setStrategies(stratRes.value);
      if (btRes.status === "fulfilled") setBacktests(btRes.value);
      if (resRes.status === "fulfilled") setResearchData(resRes.value);
      if (riskRes.status === "fulfilled") setRiskData(riskRes.value);
      if (regRes.status === "fulfilled") setRegimeData(regRes.value);
      if (audRes.status === "fulfilled") setAuditLogs(audRes.value);
    } catch (err) {
      console.warn("Telemetry loading error:", err);
    } finally {
      setIsRefreshing(false);
    }
  }, []);

  useEffect(() => {
    loadData();
    const interval = setInterval(loadData, 10000);
    return () => clearInterval(interval);
  }, [loadData]);

  const handleConfirmKill = async () => {
    try {
      await api.triggerKillSwitch();
      loadData();
    } catch (err) {
      console.error("Kill switch trigger error:", err);
    }
  };

  const handleResetKill = async () => {
    try {
      await api.resetKillSwitch();
      loadData();
    } catch (err) {
      console.error("Kill switch reset error:", err);
    }
  };

  const isKillActive = Boolean(riskData?.kill_switch_active);

  return (
    <div className="flex min-h-screen bg-background">
      <Sidebar
        currentTab={currentTab}
        onTabChange={setCurrentTab}
        killSwitchActive={isKillActive}
        onOpenKillModal={() => setIsKillModalOpen(true)}
      />

      <div className="flex-1 flex flex-col min-w-0">
        <PaperTradingBanner isLive={false} />

        <Header
          currentTab={currentTab}
          onRefresh={loadData}
          isRefreshing={isRefreshing}
          killSwitchActive={isKillActive}
          onOpenKillModal={() => setIsKillModalOpen(true)}
        />

        <main className="flex-1 p-6 overflow-y-auto">
          {currentTab === "overview" && (
            <OverviewView
              portfolio={portfolio}
              regime={regimeData}
              risk={riskData}
              positions={positions}
              history={history}
              onNavigate={setCurrentTab}
            />
          )}

          {currentTab === "portfolio" && (
            <PortfolioView portfolio={portfolio} positions={positions} />
          )}

          {currentTab === "positions" && (
            <PositionsView positions={positions} />
          )}

          {currentTab === "orders" && (
            <OrdersView orders={orders} />
          )}

          {currentTab === "strategies" && (
            <StrategiesView strategies={strategies} />
          )}

          {currentTab === "research" && (
            <ResearchLabView researchData={researchData} onRefresh={loadData} />
          )}

          {currentTab === "backtests" && (
            <BacktestsView backtests={backtests} onRefresh={loadData} />
          )}

          {currentTab === "risk" && (
            <RiskCenterView
              riskData={riskData}
              onOpenKillModal={() => setIsKillModalOpen(true)}
            />
          )}

          {currentTab === "regime" && (
            <MarketRegimeView regimeData={regimeData} />
          )}

          {currentTab === "explain" && (
            <TradeExplainView />
          )}

          {currentTab === "health" && (
            <SystemHealthView />
          )}

          {currentTab === "audit" && (
            <AuditLogView auditLogs={auditLogs} />
          )}
        </main>
      </div>

      <KillSwitchModal
        isOpen={isKillModalOpen}
        onClose={() => setIsKillModalOpen(false)}
        isKillActive={isKillActive}
        onConfirmKill={handleConfirmKill}
        onResetKill={handleResetKill}
      />
    </div>
  );
}
