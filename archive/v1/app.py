import json
import os
import time
from pathlib import Path
import streamlit as st
from engine import retrieve, analyze

ROOT = Path(__file__).resolve().parent
st.set_page_config(page_title='SIP Discovery | INDmoney', page_icon='🔎', layout='wide')
st.title('SIP Discovery')
st.caption('INDmoney · First-time mutual-fund investors · Research pilot')
st.warning('Pilot evidence, not validated findings. No investment advice. AI quality evaluation is pending.')
rows = json.loads((ROOT/'data/pilot.json').read_text())
explore, research, manual, methods = st.tabs(['Evidence explorer','Research questions','Manual labels','Method & coverage'])
with explore:
    source = st.selectbox('Source', ['All']+sorted({r['source'] for r in rows}))
    product = st.selectbox('Product', ['All']+sorted({r['product'] for r in rows}))
    query = st.text_input('Search evidence')
    filtered = [r for r in rows if (source=='All' or r['source']==source) and (product=='All' or r['product']==product) and (not query or query.lower() in json.dumps(r).lower())]
    st.write(f'{len(filtered)} of {len(rows)} pilot records. Counts describe this dataset only.')
    for r in filtered:
        with st.expander(f"{r['id']} · {r['source']} · {r['source_locator']}"):
            st.caption(f"{r['product']} | Published: {r['published_at']} | Captured: {r['captured_at']}")
            st.text('Excerpt: '+r['excerpt'])
            st.write('AI-assisted paraphrase: '+r['summary'])
            st.link_button('Open original source',r['source_url'])
            st.caption('Review ID: '+r['source_record_id']+' · '+r['verification'])
with research:
    st.info('Answers use up to 8 matching records. This is not a dataset-wide theme analysis. Citation checking verifies IDs and exact excerpts, not whether the interpretation is correct.')
    q = st.text_input('Research question',placeholder='What difficulties do users report when checking SIP investments?',max_chars=1000)
    if st.button('Find evidence and analyse'):
        evidence = retrieve(q,rows) if q.strip() else []
        if not evidence: st.warning('No matching evidence. Try a more specific question.')
        else:
            def secret(name):
                if os.environ.get(name): return os.environ[name]
                try: return st.secrets.get(name,'')
                except FileNotFoundError: return ''
            start=time.monotonic()
            try:
                with st.spinner('Reviewing evidence…'):
                    answer=analyze(q,evidence,secret('GROQ_API_KEY'),secret('GROQ_MODEL'))
                st.caption('Citation structure passed · Interpretation requires review')
                for c in answer['claims']:
                    st.write(c['text'])
                    for ref in c['evidence']: st.text(f"[{ref['id']}] {ref['quote']}")
                st.write(answer.get('limitations',''))
            except ValueError as error: st.warning(str(error))
            except Exception: st.warning('AI is temporarily unavailable. No answer was generated. You can still inspect the evidence.')
            st.caption(f'Elapsed: {time.monotonic()-start:.1f}s')
            for r in evidence:
                st.write(f"[{r['id']}] {r['summary']}")
                st.link_button('Source '+r['id'],r['source_url'])
with manual:
    st.markdown((ROOT/'docs/labelling-guide.md').read_text())
    worksheet=json.loads((ROOT/'data/manual_labels_blank.json').read_text())
    edited=st.data_editor(worksheet,disabled=['id','source_url','source_locator','excerpt','read_original_required'],hide_index=True)
    st.download_button('Download my labels',json.dumps(edited,indent=2,ensure_ascii=False),'manual_labels.json','application/json')
    st.caption('Download before closing. Labels are not automatically saved or submitted.')
with methods:
    st.json(json.loads((ROOT/'data/collection_manifest.json').read_text()))
    st.markdown((ROOT/'README.md').read_text())
