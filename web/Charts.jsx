import React, { useRef, useEffect } from 'react';
import Chart from 'chart.js/auto';

export default function Charts({ hosts }) {
  const cpuChartRef = useRef(null);
  const memChartRef = useRef(null);

  useEffect(() => {
    if (!hosts) return;
    const labels = hosts.map(h => h.hostname);
    const cpuData = hosts.map(h => parseFloat(String(h.cpu_load).split(' ')[0]) || 0);
    const memData = hosts.map(h => {
      const m = String(h.memory).match(/Mem:\s+(\d+)\s+(\d+)/);
      if (m) {
        const total = parseFloat(m[1]);
        const used = parseFloat(m[2]);
        return total ? (used / total * 100).toFixed(2) : 0;
      }
      const parts = String(h.memory).trim().split(/\s+/);
      if (parts.length >= 3) {
        const total = parseFloat(parts[1]);
        const used = parseFloat(parts[2]);
        return total ? (used / total * 100).toFixed(2) : 0;
      }
      return 0;
    });

    const cpuCtx = cpuChartRef.current;
    const memCtx = memChartRef.current;

    let cpuChart, memChart;
    if (cpuCtx) {
      cpuChart = new Chart(cpuCtx, {
        type: 'bar',
        data: {
          labels,
          datasets: [{
            label: 'CPU Load',
            data: cpuData,
            backgroundColor: 'rgba(54, 162, 235, 0.6)'
          }]
        },
        options: {
          responsive: true,
          scales: { y: { beginAtZero: true } }
        }
      });
    }

    if (memCtx) {
      memChart = new Chart(memCtx, {
        type: 'bar',
        data: {
          labels,
          datasets: [{
            label: 'Memory Usage %',
            data: memData,
            backgroundColor: 'rgba(255, 99, 132, 0.6)'
          }]
        },
        options: {
          responsive: true,
          scales: { y: { beginAtZero: true, max: 100 } }
        }
      });
    }

    return () => {
      cpuChart && cpuChart.destroy();
      memChart && memChart.destroy();
    };
  }, [hosts]);

  return (
    <div className="col-lg-4 chart-container">
      <canvas ref={cpuChartRef} id="cpuChart" height="200"></canvas>
      <canvas ref={memChartRef} id="memChart" height="200" className="mt-4"></canvas>
    </div>
  );
}
