import { useEffect, useState } from 'react';
import { ArrowDownToLine, ArrowUpRight, ChartNoAxesCombined, FileText, Printer, Search } from 'lucide-react';
import { ReportMarkdownBody } from '../components/report/ReportMarkdownBody';

interface PublishedReport {
  id: string;
  date: string;
  kind: 'stocks' | 'market';
  title: string;
  markdown: string;
  download: string;
  runUrl: string;
}

interface ReportIndex {
  publishedAt: string;
  workflowUrl: string;
  reports: PublishedReport[];
}

const kindLabel = { stocks: '个股研报', market: '大盘复盘' };

export function ReportSite() {
  const [data, setData] = useState<ReportIndex | null>(null);
  const [error, setError] = useState('');
  const [query, setQuery] = useState('');
  const [kind, setKind] = useState('all');
  const [selectedId, setSelectedId] = useState(() => new URLSearchParams(window.location.search).get('report') ?? '');

  useEffect(() => {
    const controller = new AbortController();
    fetch('./data/index.json', { signal: controller.signal, cache: 'no-cache' })
      .then(async (response) => {
        if (!response.ok) throw new Error('报告暂时无法加载，请稍后重试。');
        return response.json() as Promise<ReportIndex>;
      })
      .then(setData)
      .catch((reason: Error) => {
        if (reason.name !== 'AbortError') setError('报告暂时无法加载，请刷新页面重试。');
      });
    return () => controller.abort();
  }, []);

  useEffect(() => {
    const onPopState = () => setSelectedId(new URLSearchParams(window.location.search).get('report') ?? '');
    window.addEventListener('popstate', onPopState);
    return () => window.removeEventListener('popstate', onPopState);
  }, []);

  const reports = data?.reports ?? [];
  const selected = reports.find((report) => report.id === selectedId) ?? reports[0];
  const searchTerm = query.trim().toLowerCase();
  const filtered = reports.filter((report) => (
    (kind === 'all' || report.kind === kind)
    && `${report.date} ${report.title} ${report.markdown}`.toLowerCase().includes(searchTerm)
  ));

  function selectReport(report: PublishedReport) {
    setSelectedId(report.id);
    const target = new URL(window.location.href);
    target.searchParams.set('report', report.id);
    window.history.pushState(null, '', target);
    document.getElementById('report-heading')?.focus({ preventScroll: true });
  }

  return (
    <>
      <a className="skip-link" href="#report-heading">跳至报告正文</a>
      <header className="site-header">
        <a className="brand" href="./" aria-label="投研日报首页">
          <span className="brand-mark"><ChartNoAxesCombined size={23} strokeWidth={1.8} /></span>
          <span>投研日报<span className="brand-divider">/</span><span className="brand-initials">DSA</span></span>
        </a>
        <span className="header-note">每日分析 · 持续归档</span>
        {data && <a className="text-link" href={data.workflowUrl} target="_blank" rel="noreferrer">分析任务 <ArrowUpRight size={16} /></a>}
      </header>

      <main className="workspace">
        <section className="page-intro" aria-label="报告概览">
          <div><p className="eyebrow">你的每日市场观察</p><h1>读懂行情，再做决定。</h1><p>自选股研报与大盘复盘，在这里按日期更新。</p></div>
          <div className="latest-date"><span>最新报告</span><strong>{reports[0]?.date.replaceAll('-', '.') ?? '—'}</strong><span>{reports.length ? `已归档 ${reports.length} 份报告` : '正在同步报告'}</span></div>
        </section>

        {error ? <div className="status-panel" role="alert">{error}<button onClick={() => window.location.reload()}>重新加载</button></div>
          : !data ? <div className="status-panel" role="status">正在加载每日研报…</div>
            : <div className="reading-layout">
              <aside className="archive" aria-label="历史报告">
                <div className="archive-title"><h2>报告归档</h2><span>{reports.length}</span></div>
                <label className="search-box"><Search size={17} /><input value={query} onChange={(event) => setQuery(event.target.value)} placeholder="搜索股票、日期或内容" aria-label="搜索报告" /></label>
                <div className="filters" aria-label="报告类型">
                  {([['all', '全部'], ['stocks', '个股'], ['market', '大盘']] as const).map(([value, label]) => <button key={value} aria-pressed={kind === value} onClick={() => setKind(value)}>{label}</button>)}
                </div>
                <nav className="report-list" aria-label="选择报告">
                  {filtered.map((report, index) => <button className={`report-option ${selected?.id === report.id ? 'selected' : ''}`} key={report.id} onClick={() => selectReport(report)} aria-current={selected?.id === report.id ? 'page' : undefined}>
                    <span className="report-option-date">{report.date}<FileText size={16} /></span>
                    <span>{kindLabel[report.kind]}{index === 0 && report.id === reports[0]?.id && <small>最新</small>}</span>
                  </button>)}
                  {!filtered.length && <p className="empty-search">没有找到匹配的报告。试试其他日期或股票代码。</p>}
                </nav>
                <p className="archive-note">报告完成后自动更新。<br />保留最近 30 天可用的分析记录。</p>
              </aside>

              {selected ? <section className="report-panel" aria-label="报告正文">
                <div className="report-toolbar"><div><span className="report-kind">{kindLabel[selected.kind]}</span><span className="toolbar-date">{selected.date}</span></div><div className="report-actions"><button onClick={() => window.print()} aria-label="打印报告"><Printer size={16} /><span>打印</span></button><a href={`./data/${selected.download}`} download><ArrowDownToLine size={16} /><span>下载原文</span></a></div></div>
                <div className="report-content" id="report-heading" tabIndex={-1}>
                  <ReportMarkdownBody content={selected.markdown} className="published-markdown" />
                </div>
                <div className="report-footer"><span>本报告仅供研究参考，不构成投资建议。</span><a href={selected.runUrl} target="_blank" rel="noreferrer">查看生成记录 <ArrowUpRight size={14} /></a></div>
              </section> : <div className="status-panel">暂无已生成的报告。</div>}
            </div>}

        <footer className="site-footer"><span>DSA · Daily Stock Analysis</span><span>{data ? `页面更新于 ${new Intl.DateTimeFormat('zh-CN', { timeZone: 'Asia/Shanghai', dateStyle: 'medium', timeStyle: 'short', hour12: false }).format(new Date(data.publishedAt))}（北京时间）` : '每日股票分析'}</span></footer>
      </main>
    </>
  );
}
