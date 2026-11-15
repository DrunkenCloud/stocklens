"use client";

import { AreaSeries, ColorType, CrosshairMode, LineSeries, LineStyle, LineType, createChart, type Time } from "lightweight-charts";
import { useEffect, useRef } from "react";

import { useThemeColors, withAlpha } from "@/hooks/use-theme-colors";
import { inrCompact } from "@/lib/format";

export interface SeriesPoint {
  time: string;
  value: number;
}

export function TimeSeriesChart({
  data, secondary, height = 280, reference, onHover, formatPrice = inrCompact,
}: {
  data: SeriesPoint[];
  secondary?: SeriesPoint[];
  height?: number;
  reference?: { value: number; label: string } | null;
  onHover?: (point: SeriesPoint | null) => void;
  formatPrice?: (v: number) => string;
}) {
  const container = useRef<HTMLDivElement>(null);
  const colors = useThemeColors();
  const hoverRef = useRef(onHover);
  const formatRef = useRef(formatPrice);
  useEffect(() => {
    hoverRef.current = onHover;
    formatRef.current = formatPrice;
  });

  const rising = data.length < 2 || data[data.length - 1].value >= data[0].value;

  useEffect(() => {
    if (!container.current || !colors || data.length === 0) return;
    const line = rising ? colors["--gain"] : colors["--loss"];
    const chart = createChart(container.current, {
      autoSize: true,
      layout: {
        background: { type: ColorType.Solid, color: "transparent" },
        textColor: colors["--muted-foreground"],
        fontFamily: getComputedStyle(document.body).fontFamily,
        fontSize: 11,
      },
      grid: { vertLines: { visible: false }, horzLines: { color: colors["--border"] } },
      rightPriceScale: { borderVisible: false, scaleMargins: { top: 0.12, bottom: 0.04 } },
      timeScale: { borderVisible: false, fixLeftEdge: true, fixRightEdge: true },
      crosshair: {
        mode: CrosshairMode.Magnet,
        vertLine: { color: colors["--text-tertiary"], style: LineStyle.Dashed, width: 1, labelVisible: false },
        horzLine: { visible: false, labelVisible: false },
      },
      handleScroll: false,
      handleScale: false,
      localization: { priceFormatter: (p: number) => formatRef.current(p) },
    });
    const series = chart.addSeries(AreaSeries, {
      lineColor: line,
      lineWidth: 2,
      topColor: withAlpha(line, 0.2),
      bottomColor: withAlpha(line, 0),
      priceLineVisible: false,
      lastValueVisible: false,
      crosshairMarkerRadius: 4,
      crosshairMarkerBorderColor: colors["--surface"],
    });
    series.setData(data.map((d) => ({ time: d.time as Time, value: d.value })));
    if (secondary?.length) {
      const line = chart.addSeries(LineSeries, {
        color: colors["--muted-foreground"],
        lineWidth: 1,
        lineType: LineType.WithSteps,
        lineStyle: LineStyle.Dashed,
        priceLineVisible: false,
        lastValueVisible: false,
        crosshairMarkerVisible: false,
      });
      line.setData(secondary.map((d) => ({ time: d.time as Time, value: d.value })));
    }
    if (reference) {
      series.createPriceLine({
        price: reference.value,
        color: colors["--text-tertiary"],
        lineStyle: LineStyle.Dashed,
        lineWidth: 1,
        axisLabelVisible: false,
        title: reference.label,
      });
    }
    chart.timeScale().fitContent();
    chart.subscribeCrosshairMove((param) => {
      const point = param.seriesData.get(series) as { value?: number } | undefined;
      hoverRef.current?.(param.time && point?.value !== undefined ? { time: String(param.time), value: point.value } : null);
    });
    return () => chart.remove();
  }, [data, secondary, colors, rising, reference]);

  return <div ref={container} style={{ height }} className="w-full" />;
}
