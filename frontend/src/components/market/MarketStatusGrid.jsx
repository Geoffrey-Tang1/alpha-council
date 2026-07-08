import { useEffect, useState } from "react";
import { useTranslation } from "react-i18next";

import { formatMarketLocalTime } from "../../utils/formatting.js";
import Card from "../ui/Card.jsx";
import MarketStatusBadge from "./MarketStatusBadge.jsx";

export default function MarketStatusGrid({ markets = [] }) {
  const { i18n, t } = useTranslation();
  const [now, setNow] = useState(() => new Date());

  useEffect(() => {
    const interval = setInterval(() => setNow(new Date()), 60000);
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="market-grid">
      {markets.map((market) => {
        const display = {
          country: t(`markets.${market.market}.country`, { defaultValue: market.display_name || market.market }),
          city: t(`markets.${market.market}.city`, { defaultValue: market.market }),
          timezoneLabel: t(`markets.${market.market}.timezone`, { defaultValue: market.timezone })
        };
        const formattedLocalTime = formatMarketLocalTime(market.timezone, now, i18n.resolvedLanguage || i18n.language);
        const localTime =
          formattedLocalTime === "Local time unavailable" ? t("markets.localTimeUnavailable") : formattedLocalTime;

        return (
          <Card key={market.market} className="market-card">
            <div className="market-card-header">
              <div className="market-card-title">
                <p className="eyebrow">{market.market}</p>
                <h3>{display.country}</h3>
              </div>
              <MarketStatusBadge status={market.status} />
            </div>
            <div className="market-clock-block" aria-label={`${display.city}, ${display.timezoneLabel}, ${localTime}`}>
              <div className="market-clock-label">
                <span className="market-city">{display.city}</span>
                <span className="dot-separator">·</span>
                <span className="market-timezone">{display.timezoneLabel}</span>
              </div>
              <div className="market-local-time">{localTime}</div>
            </div>
            <p className="market-session">
              {t("markets.regularSession", {
                open: market.session.regular_open,
                close: market.session.regular_close
              })}
            </p>
          </Card>
        );
      })}
    </div>
  );
}
