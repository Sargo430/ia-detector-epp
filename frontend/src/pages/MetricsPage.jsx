import React, { useMemo } from 'react'
import {
  Chart as ChartJS,
  CategoryScale, LinearScale, BarElement,
  ArcElement, Tooltip, Legend,
} from 'chart.js'
import { Bar, Doughnut } from 'react-chartjs-2'
import { MetricCard } from '../components/UI.jsx'
import { EVENT_TYPES, EVENT_LABELS, CHART_COLORS } from '../lib/constants.js'

ChartJS.register(CategoryScale, LinearScale, BarElement, ArcElement, Tooltip, Legend)

const HOUR_LABELS = Array.from({ length: 24 }, (_, i) => `${String(i).padStart(2, '0')}h`)
const SEED_HOURS  = Array.from({ length: 24 }, () => Math.floor(Math.random() * 18) + 1)

export default function MetricsPage({ stats }) {
  const { totalEvents, criticalCount, latency } = stats

  const hourData = useMemo(() => {
    const data = [...SEED_HOURS]
    data[new Date().getHours()] = totalEvents % 24
    return data
  }, [totalEvents])

  const typeData   = [22, 14, 6, 3, 2]
  const typeLabels = EVENT_TYPES.map(t => EVENT_LABELS[t])

  const barData = {
    labels: HOUR_LABELS,
    datasets: [{
      label: 'Eventos',
      data: hourData,
      backgroundColor: 'rgba(46,168,156,.55)',
      borderColor: '#2ea89c',
      borderWidth: 1,
      borderRadius: 3,
    }],
  }

  const barOpts = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: { legend: { display: false } },
    scales: {
      x: { ticks: { color: '#6e7681', font: { size: 10 }, maxRotation: 0 }, grid: { color: 'rgba(48,54,61,.5)' }, border: { display: false } },
      y: { ticks: { color: '#6e7681', font: { size: 10 } },               grid: { color: 'rgba(48,54,61,.5)' }, border: { display: false } },
    },
  }

  const donutData = {
    labels: typeLabels,
    datasets: [{
      data: typeData,
      backgroundColor: CHART_COLORS,
      borderWidth: 2,
      borderColor: '#161b22',
    }],
  }

  const donutOpts = {
    responsive: true,
    maintainAspectRatio: false,
    cutout: '62%',
    plugins: { legend: { display: false } },
  }

  return (
    <div>
      {/* Metric cards row */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4,1fr)', gap: 12, marginBottom: 20 }}>
        <MetricCard
          label="Cámaras activas"
          value={<>5<span style={{ fontSize: 14, color: 'var(--text3)' }}>/6</span></>}
          sub="83% online"
          subVariant="up"
        />
        <MetricCard
          label="Eventos hoy"
          value={totalEvents}
          sub="↑ 12 vs ayer"
        />
        <MetricCard
          label="Alertas críticas"
          value={<span style={{ color: 'var(--red)' }}>{criticalCount}</span>}
          sub="Sin resolver"
          subVariant="down"
        />
        <MetricCard
          label="Latencia edge"
          value={<span style={{ color: 'var(--teal2)' }}>{latency ?? '--'}</span>}
          sub="ms · edge → cloud"
        />
      </div>

      {/* Charts row */}
      <div style={{ display: 'grid', gridTemplateColumns: '1.6fr 1fr', gap: 16 }}>
        <ChartCard title="Eventos por hora (últimas 24h)">
          <div style={{ position: 'relative', height: 200 }}>
            <Bar data={barData} options={barOpts}
              aria-label="Gráfico de barras: eventos detectados por hora en las últimas 24 horas" />
          </div>
        </ChartCard>

        <ChartCard title="Distribución por tipo">
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8, marginBottom: 10 }}>
            {EVENT_TYPES.map((t, i) => (
              <span key={t} style={{ display: 'flex', alignItems: 'center', gap: 4, fontSize: 11, color: 'var(--text2)' }}>
                <span style={{ width: 8, height: 8, borderRadius: 2, background: CHART_COLORS[i], display: 'inline-block' }} />
                {EVENT_LABELS[t]}
              </span>
            ))}
          </div>
          <div style={{ position: 'relative', height: 170 }}>
            <Doughnut data={donutData} options={donutOpts}
              aria-label="Gráfico de dona: distribución de eventos por tipo" />
          </div>
        </ChartCard>
      </div>
    </div>
  )
}

function ChartCard({ title, children }) {
  return (
    <div style={{ background: 'var(--bg2)', border: '1px solid var(--border)', borderRadius: 'var(--r2)', padding: 16 }}>
      <div style={{ fontSize: 13, fontWeight: 500, color: 'var(--text2)', marginBottom: 14 }}>{title}</div>
      {children}
    </div>
  )
}
