"""Run the published example through the engine and published JSON schemas."""
import csv
import json
import socket
from pathlib import Path
from jsonschema import Draft202012Validator
from gtm_outreach_kit.engine import prepare

ROOT=Path(__file__).resolve().parents[1]
ASSETS=ROOT/'gtm_outreach_kit'/'assets'
EXPECTED={'input_rows':100,'unique_records':90,'duplicate_rows':10,'qualified':31,'review':32,'excluded':27,'suppressed':2,'drafts':24}

def validate(name,value):
    schema=json.loads((ROOT/'docs'/'schemas'/f'{name}.schema.json').read_text())
    Draft202012Validator.check_schema(schema)
    Draft202012Validator(schema).validate(value)

def main():
    def blocked(*a,**k):
        raise AssertionError('Offline demo attempted to use the network')
    socket.socket=blocked
    socket.create_connection=blocked
    validate('brief',json.loads((ASSETS/'brief.json').read_text()))
    for name in ['prospect','signal','suppression']:
        filename={'prospect':'prospects','signal':'signals','suppression':'suppressions'}[name]
        with (ASSETS/f'{filename}.csv').open() as f:
            for row in csv.DictReader(f):
                validate(name+'-row',row)
    run=prepare(ASSETS/'prospects.csv',ASSETS/'brief.json',signals_path=ASSETS/'signals.csv',suppressions_path=ASSETS/'suppressions.csv',as_of='2026-10-29')
    validate('run',run)
    assert run['summary']==EXPECTED, run['summary']
    assert all(r['fit_status']=='qualified' and r['contact_status']=='syntax_only' for r in run['records'] if r['id'] in {d['record_id'] for d in run['drafts']})
    print('PASS: schemas, 100-row offline demo, expected dispositions and draft eligibility.')

if __name__=='__main__':
    main()
