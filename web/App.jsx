import React, { useState, useEffect, useCallback } from 'react';
import Charts from './Charts';

function fetchData(search, sort, order) {
  const params = new URLSearchParams();
  if (search) params.set('search', search);
  if (sort) params.set('sort', sort);
  if (order) params.set('order', order);
  const url = '/api/hosts?' + params.toString();
  return fetch(url).then(r => r.json());
}

export default function App() {
  const [data, setData] = useState([]);
  const [search, setSearch] = useState('');
  const [cpuFilter, setCpuFilter] = useState('');
  const [sortKey, setSortKey] = useState('hostname');
  const [sortDir, setSortDir] = useState('asc');

  const load = useCallback(() => {
    fetchData(search, sortKey, sortDir).then(setData);
  }, [search, sortKey, sortDir]);

  useEffect(() => {
    load();
    const t = setInterval(load, 30000);
    return () => clearInterval(t);
  }, [load]);

  const handleSort = key => {
    if (sortKey === key) {
      setSortDir(sortDir === 'asc' ? 'desc' : 'asc');
    } else {
      setSortKey(key);
      setSortDir('asc');
    }
  };

  const filtered = data
    .filter(h => h.hostname.toLowerCase().includes(search.toLowerCase()))
    .filter(h =>
      cpuFilter ? parseFloat(h.cpu_load) <= parseFloat(cpuFilter) : true
    );

  return (
    <div>
      <h1 className="mb-4">Collected System Facts</h1>
      <div className="row g-2 mb-3">
        <div className="col-md-6">
          <input
            className="form-control"
            placeholder="Search host"
            value={search}
            onChange={e => setSearch(e.target.value)}
          />
        </div>
        <div className="col-md-6">
          <input
            className="form-control"
            placeholder="Max CPU load"
            value={cpuFilter}
            onChange={e => setCpuFilter(e.target.value)}
          />
        </div>
      </div>
      <div className="row">
        <div className="col-lg-8">
          <table className="table table-striped table-bordered">
            <thead className="table-light">
              <tr>
                <th onClick={() => handleSort('hostname')}>Hostname</th>
                <th onClick={() => handleSort('cpu_load')}>CPU Load</th>
                <th onClick={() => handleSort('memory')}>Memory</th>
                <th onClick={() => handleSort('disk')}>Disk</th>
                <th>Users</th>
                <th>Listening Ports</th>
                <th>Network</th>
                <th>Sensors</th>
              </tr>
            </thead>
            <tbody>
              {filtered.map((h, i) => (
                <tr key={i}>
                  <td>{h.hostname}</td>
                  <td>{h.cpu_load}</td>
                  <td>{h.memory}</td>
                  <td>{h.disk}</td>
                  <td>
                    <ul className="mb-0">{h.users.map((u, j) => <li key={j}>{u}</li>)}</ul>
                  </td>
                  <td>
                    <ul className="mb-0">{h.ports.map((p, j) => <li key={j}>{p}</li>)}</ul>
                  </td>
                  <td>
                    <ul className="mb-0">{h.net.map((n, j) => <li key={j}>{n}</li>)}</ul>
                  </td>
                  <td>
                    <ul className="mb-0">{h.sensors.map((s, j) => <li key={j}>{s}</li>)}</ul>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        <Charts hosts={filtered} />
      </div>
    </div>
  );
}
