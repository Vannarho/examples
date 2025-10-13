import sys
from pathlib import Path
import pandas as pd
import xml.etree.ElementTree as ET
from datetime import datetime
from IPython.display import Markdown, display

def format_report(report):
    import pandas as _pd
    headers = [(i, report.header(i), report.columnType(i)) for i in range(report.columns())]
    data = {}
    for i, name, t in headers:
        if t == 0:
            data[name] = list(report.dataAsSize(i))
        elif t == 1:
            data[name] = list(report.dataAsReal(i))
        elif t == 2:
            data[name] = list(report.dataAsString(i))
        elif t == 3:
            data[name] = [d.ISO() for d in report.dataAsDate(i)]
        elif t == 4:
            data[name] = list(report.dataAsPeriod(i))
    return _pd.DataFrame(data)

_DEF_SEARCH_ROOTS = [Path.cwd()] + [p for p in Path.cwd().parents][:4]

def resolve(relpath: str) -> str:
    rel = Path(relpath)
    if rel.is_absolute() and rel.exists():
        return str(rel)
    if rel.exists():
        return str(rel)
    for root in _DEF_SEARCH_ROOTS:
        cand = root / relpath
        if cand.exists():
            return str(cand)
    for root in _DEF_SEARCH_ROOTS:
        for c in root.rglob(rel.name):
            if rel.name == c.name:
                return str(c)
    return relpath

def list_reports(app):
    try:
        names = sorted(list(app.getReportNames()))
        for n in names:
            print('-', n)
    except Exception as e:
        print('getReportNames failed:', e)

def show_report(app, name, head=20, quiet=True):
    from pathlib import Path as _Path
    bases = []
    try:
        outp = app.outputsPath()
        if outp:
            bases.append(_Path(outp))
    except Exception:
        pass
    bases.extend(_DEF_SEARCH_ROOTS)
    # In-memory first
    try:
        r = app.getReport(name)
        df = format_report(r)
        display(df.head(head))
        return True
    except Exception:
        pass
    # CSV fallback
    for root in bases:
        for p in root.rglob(f"{name}*.csv"):
            # Skip supervisory correlation tables (CRE52) if present in same folder
            if 'cre52' in p.name.lower():
                continue
            try:
                display(pd.read_csv(p).head(head))
                return True
            except Exception:
                pass
    # Special-case known FRTB-SA layout
    for extra in ['Examples/MarketRisk/Output/FRTB_SA/SBM','Examples/MarketRisk/Output/FRTB_SA/Simplified']:
        rp = _Path(extra) / f"{name}.csv"
        if rp.exists():
            try:
                display(pd.read_csv(rp).head(head))
                return True
            except Exception:
                pass
    if not quiet:
        print('No CSV or in-memory report for', name)
    return False

def describe_portfolio(app, max_chars=2000):
    try:
        inputs = getattr(app, 'getInputs', lambda: None)()
        if not inputs:
            return  # not available for Parameters-based runs
        port = inputs.portfolio()
        if not port:
            return
        ids = list(port.ids())
        print(f'Trades: {port.size()}\n')
        types = {}
        for tid in ids:
            t = port.get(tid)
            types[t.tradeType()] = types.get(t.tradeType(), 0) + 1
        print('By type:', ', '.join([f"{k}={v}" for k,v in types.items()]))
        xml = port.toXMLString()
        flags = []
        for kw in ['CSA', 'Collateral', 'Margin', 'NettingSet', 'Agreement']:
            if kw.lower() in xml.lower():
                flags.append(kw)
        if flags:
            print('CSA/Collateral hints:', ', '.join(sorted(set(flags))))
        else:
            print('CSA/Collateral hints: none detected in trade XML')
    except Exception as e:
        print('describe_portfolio failed:', e)

def _parse_first_param(xml_root, names):
    vals = {}
    for p in xml_root.findall('.//Parameter'):
        name = p.attrib.get('name')
        if name in names and name not in vals:
            vals[name] = (p.text or '').strip()
    return vals

def _summarize_portfolio_file(file_path):
    try:
        root = ET.parse(file_path).getroot()
        trades = root.findall('.//Trade')
        types = {}
        netting = set()
        ccys = set()
        for t in trades:
            tt = (t.findtext('TradeType') or '').strip()
            types[tt] = types.get(tt, 0) + 1
            ns = t.find('.//NettingSetId')
            if ns is not None and ns.text:
                netting.add(ns.text.strip())
            for c in t.findall('.//Currency'):
                if c.text:
                    ccys.add(c.text.strip())
        print(f"Portfolio file: {file_path}")
        print(f"Trades: {len(trades)} | By type: ", ', '.join([f"{k}={v}" for k,v in types.items()]) or 'n/a')
        if ccys:
            print('Currencies:', ', '.join(sorted(ccys)))
        if netting:
            print('Netting sets:', ', '.join(sorted(netting)))
    except Exception as e:
        print('Could not summarize portfolio:', file_path, e)

def describe_master_portfolio(master_xml_path, quiet: bool = False):
    """Parse a master XML and print portfolio and CSA/collateral config with basic summary.

    Respects <Setup><Parameter name="inputPath">...</Parameter> for relative saccr/portfolio files.
    """
    try:
        mpath = Path(resolve(master_xml_path))
        root = ET.parse(mpath).getroot()
        # Resolve bases: master folder and optional setup inputPath
        setup_params = _parse_first_param(root, {'inputPath'})
        bases = [mpath.parent]
        setup_ip = setup_params.get('inputPath')
        if setup_ip:
            # Typical masters sit under .../Examples/<Domain>/Input, with inputPath like "Input/SA-CCR"
            # Prefer parent-of-Input joined to inputPath, then fallback to sibling under current parent
            parent_of_input = mpath.parent.parent  # e.g., Examples/CreditRisk
            bases.insert(0, (parent_of_input / setup_ip))
            bases.append(mpath.parent / setup_ip)

        params = _parse_first_param(root, {
            'portfolioFile','saccrPortfolioFile','saccrCsaFile','saccrCollateralBalancesFile','saccrBaseCurrency'
        })

        def resolve_from_bases(rel):
            if not rel:
                return None
            for b in bases:
                cand = (Path(b) / rel)
                if cand.exists():
                    return cand
            return Path(bases[-1]) / rel  # best-effort

        # Portfolio file preference: saccrPortfolioFile (SA-CCR) then portfolioFile
        pf_rel = params.get('saccrPortfolioFile') or params.get('portfolioFile')
        pfile = resolve_from_bases(pf_rel) if pf_rel else None
        if (not pfile or not pfile.exists()) and pf_rel:
            # Robust fallback: search upward from domain root for the filename
            fname = Path(pf_rel).name
            for root in {mpath.parent, mpath.parent.parent} | set(_DEF_SEARCH_ROOTS):
                for hit in Path(root).rglob(fname):
                    pfile = hit
                    break
                if pfile and pfile.exists():
                    break
        if pfile and pfile.exists():
            _summarize_portfolio_file(pfile)

        # CSA / collateral files
        csa_rel = params.get('saccrCsaFile')
        coll_rel = params.get('saccrCollateralBalancesFile')
        csa = resolve_from_bases(csa_rel) if csa_rel else None
        coll = resolve_from_bases(coll_rel) if coll_rel else None
        # Fallback search for CSA/collateral files if not found at bases
        if csa_rel and (not csa or not csa.exists()):
            fname = Path(csa_rel).name
            for root in {mpath.parent, mpath.parent.parent} | set(_DEF_SEARCH_ROOTS):
                for hit in Path(root).rglob(fname):
                    csa = hit
                    break
                if csa and csa.exists():
                    break
        if coll_rel and (not coll or not coll.exists()):
            fname = Path(coll_rel).name
            for root in {mpath.parent, mpath.parent.parent} | set(_DEF_SEARCH_ROOTS):
                for hit in Path(root).rglob(fname):
                    coll = hit
                    break
                if coll and coll.exists():
                    break
        if csa and not quiet:
            print('CSA definition file:', csa)
        if coll and not quiet:
            print('Collateral balances file:', coll)
        if not (pf_rel or csa_rel or coll_rel) and not quiet:
            print('No explicit portfolio/CSA parameters found in master XML.')
    except Exception as e:
        if not quiet:
            print('describe_master_portfolio failed:', e)

def _display_csv(path, head=20, title=None):
    try:
        import pandas as _pd
        if title:
            print(title, '->', path)
        display(_pd.read_csv(path).head(head))
        return True
    except Exception:
        return False

def show_saccr_triplet(tag_hint=None, head=20):
    roots = [Path('Examples/CreditRisk/Output/SA-CCR')] + _DEF_SEARCH_ROOTS
    outs = [r for r in roots if Path(r).exists()]
    def pick_exact(root, prefix, ext):
        if tag_hint:
            candidate = Path(root) / f"{prefix}_{tag_hint}.{ext}"
            if candidate.exists():
                return candidate
        return None
    def pick_latest(files):
        if not files:
            return None
        files.sort(key=lambda p: p.stat().st_mtime, reverse=True)
        return files[0]
    # Prefer exact filenames when tag_hint is provided
    csv_main = None
    csv_crif = None
    json_tree = None
    for root in outs:
        if not csv_main:
            csv_main = pick_exact(root, 'saccr_output', 'csv')
        if not csv_crif:
            csv_crif = pick_exact(root, 'saccr_crif', 'csv')
        if not json_tree:
            json_tree = pick_exact(root, 'saccr_output', 'json')
    # Fallback to latest matching files under all roots
    if not csv_main:
        csv_main = pick_latest([p for root in outs for p in Path(root).rglob('saccr_output*.csv') if (not tag_hint or tag_hint in p.name)])
    if not csv_crif:
        csv_crif = pick_latest([p for root in outs for p in Path(root).rglob('saccr_crif*.csv') if (not tag_hint or tag_hint in p.name)])
    if not json_tree:
        json_tree = pick_latest([p for root in outs for p in Path(root).rglob('saccr_output*.json') if (not tag_hint or tag_hint in p.name)])
    shown = False
    if csv_main and _display_csv(csv_main, head=head, title='SA-CCR output'):
        shown = True
    if csv_crif and _display_csv(csv_crif, head=head, title='CRIF'):
        shown = True
    if json_tree:
        try:
            import json as _json
            print('JSON tree ->', json_tree)
            with open(json_tree) as f:
                j = _json.load(f)
            print(_json.dumps(j if isinstance(j, dict) else {'root': j}, indent=2)[:1000] + '...')
            shown = True
        except Exception:
            pass
    if not shown:
            print('SA-CCR triplet not found (try running the example first).')

def _text(elem):
    return (elem.text or '').strip() if elem is not None else ''

def _ymd(s):
    # Accept YYYYMMDD or YYYY-MM-DD
    s = s.strip()
    for fmt in ('%Y%m%d','%Y-%m-%d'):
        try:
            return datetime.strptime(s, fmt)
        except Exception:
            pass
    return None

def portfolio_markdown_from_file(portfolio_file: Path) -> str:
    root = ET.parse(portfolio_file).getroot()
    lines = []
    lines.append(f"Portfolio file: `{portfolio_file}`\n")
    lines.append("| TradeId | Type | Currency | Notional | Start | End | Payer/PayLeg | Receive/RecLeg | Notes |")
    lines.append("|---|---|---|---:|---|---|---|---|---|")
    for t in root.findall('.//Trade'):
        tid = t.attrib.get('id','')
        ttype = _text(t.find('TradeType'))
        note = ''
        ccy = notional = start = end = payleg = recvleg = ''
        if ttype == 'Swap' or t.find('SwapData') is not None:
            legs = t.findall('.//SwapData/LegData')
            if len(legs) >= 2:
                L1, L2 = legs[0], legs[1]
                # leg1
                c1 = _text(L1.find('Currency')); n1 = _text(L1.find('.//Notional'))
                p1 = _text(L1.find('Payer'))
                lt1 = _text(L1.find('LegType'))
                s1 = _text(L1.find('.//StartDate')); e1 = _text(L1.find('.//EndDate'))
                # leg2
                c2 = _text(L2.find('Currency')); n2 = _text(L2.find('.//Notional'))
                p2 = _text(L2.find('Payer'))
                lt2 = _text(L2.find('LegType'))
                s2 = _text(L2.find('.//StartDate')); e2 = _text(L2.find('.//EndDate'))
                ccy = ','.join(sorted({c for c in [c1,c2] if c}))
                notional = n1 or n2
                start = s1 or s2; end = e1 or e2
                payleg = f"{lt1 if p1=='true' else lt2}"
                recvleg = f"{lt2 if p1=='true' else lt1}"
        elif ttype == 'Swaption' or t.find('SwaptionData') is not None:
            # Take underlying fixed/floating legs
            legs = t.findall('.//SwaptionData/LegData')
            if legs:
                ccy = ','.join(sorted({ _text(L.find('Currency')) for L in legs if _text(L.find('Currency')) }))
                notional = _text(legs[0].find('.//Notional'))
                start = _text(legs[0].find('.//StartDate')); end = _text(legs[0].find('.//EndDate'))
                payleg = _text(legs[0].find('LegType')); recvleg = _text(legs[1].find('LegType')) if len(legs)>1 else ''
                note = 'Physically-settled European'
        elif ttype == 'CreditDefaultSwap' or t.find('CreditDefaultSwapData') is not None:
            ccy = _text(t.find('.//LegData/Currency'))
            notional = _text(t.find('.//LegData/Notional'))
            start = _text(t.find('.//ScheduleData//StartDate')); end = _text(t.find('.//ScheduleData//EndDate'))
            payleg = 'Buyer' if _text(t.find('.//Payer'))=='true' else 'Seller'
            recvleg = 'Premium leg'
            note = f"Ref: {_text(t.find('.//IssuerId'))}"
        elif ttype == 'CommodityForward' or t.find('CommodityForwardData') is not None:
            ccy = _text(t.find('.//Currency'))
            notional = _text(t.find('.//Quantity'))
            start = ''
            end = _text(t.find('.//Maturity'))
            payleg = _text(t.find('.//Position'))
            recvleg = ''
            note = _text(t.find('.//Name'))
        lines.append(f"| {tid} | {ttype} | {ccy} | {notional} | {start} | {end} | {payleg} | {recvleg} | {note} |")
    return "\n".join(lines)

def display_portfolio_description(master_xml_path):
    try:
        mpath = Path(resolve(master_xml_path))
        root = ET.parse(mpath).getroot()
        setup_params = _parse_first_param(root, {'inputPath'})
        bases = [mpath.parent, mpath.parent.parent]
        setup_ip = setup_params.get('inputPath')
        if setup_ip:
            bases.insert(0, (mpath.parent.parent / setup_ip))
        params = _parse_first_param(root, {'saccrPortfolioFile','portfolioFile'})
        pf_rel = params.get('saccrPortfolioFile') or params.get('portfolioFile')
        pfile = None
        for b in bases:
            cand = Path(b) / (pf_rel or '')
            if cand.exists():
                pfile = cand; break
        if not pfile and pf_rel:
            # filename search
            fname = Path(pf_rel).name
            for rootdir in bases + _DEF_SEARCH_ROOTS:
                for hit in Path(rootdir).rglob(fname):
                    pfile = hit; break
                if pfile: break
        if pfile and pfile.exists():
            md = portfolio_markdown_from_file(pfile)
            display(Markdown(md))
        else:
            display(Markdown(f"_Portfolio file not found in master `{mpath}`_"))
    except Exception as e:
        display(Markdown(f"_Could not render portfolio description: {e}_"))
