"""Publish the v1 interchange contracts; semantic checks also live in the engine."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = 'https://json-schema.org/draft/2020-12/schema'
S = {'type': 'string'}
TEXT = {'type': 'string', 'minLength': 1}
DATE = {'type': 'string', 'pattern': r'^\d{4}-\d{2}-\d{2}$'}
INTEGER = {'type': 'integer', 'minimum': 0}
FIELDS = ['contact_id','first_name','email','company','domain','industry','employees','country','role','source_ref','observed_at']

def obj(props, required=None, extra=False):
    return {'type':'object','properties':props,'required':list(props) if required is None else required,'additionalProperties':extra}

def array(items):
    return {'type':'array','items':items}

def save(name, schema):
    schema = {'$schema':BASE,'title':name,**schema}
    p = ROOT / 'docs' / 'schemas' / (name + '.schema.json')
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(schema, indent=2)+'\n')

def main():
    numeric={'type':'integer','minimum':0}
    rule=obj({'id':{'type':'string','pattern':'^[a-z][a-z0-9-]*$'},'field':{'enum':FIELDS[:-2]},'op':{'enum':['equals','in','range']},'value':{} })
    rule['allOf']=[
      {'if':{'properties':{'field':{'const':'employees'}}},'then':{'properties':{'value':{'oneOf':[numeric,{'type':'array','minItems':1,'items':numeric}]}}},'else':{'properties':{'value':{'oneOf':[TEXT,{'type':'array','minItems':1,'items':TEXT}]}}}},
      {'if':{'properties':{'op':{'const':'range'}}},'then':{'properties':{'field':{'const':'employees'},'value':{'type':'array','minItems':2,'maxItems':2,'items':numeric}}}},
      {'if':{'properties':{'op':{'const':'in'}}},'then':{'properties':{'value':{'type':'array','minItems':1}}}},
      {'if':{'properties':{'op':{'const':'equals'}}},'then':{'properties':{'value':{'type':['string','integer']}}}}
    ]
    brief=obj({'schema_version':{'const':'1.0'},'name':TEXT,'offer':obj({'summary':TEXT,'proof_points':array(TEXT)},[]),
      'sender':obj({'name':TEXT,'company':TEXT},[]),'required':{'type':'array','minItems':1,'items':rule},
      'preferences':array(rule),'exclusions':array(rule),'column_map':obj({k:TEXT for k in FIELDS},[]),
      'signal_types':array(TEXT),'signal_max_age_days':INTEGER,'evidence_max_age_days':INTEGER,
      'templates':obj({'subject':TEXT,'first':TEXT,'follow_up':TEXT},[])},['schema_version','name','required'])
    save('brief',brief)
    values=obj({k:({'type':['integer','null'],'minimum':0} if k=='employees' else {'type':['string','null']}) for k in FIELDS})
    source=obj({'row_id':TEXT,'raw':{'type':'object','additionalProperties':S},'values':values,'problems':array(S)})
    evidence=obj({'row_id':TEXT,'source_ref':S,'observed_at':S,'value':{'type':['string','integer','null']} })
    unusable=obj({**evidence['properties'],'reason':TEXT})
    result=obj({'rule_id':TEXT,'field':TEXT,'op':TEXT,'expected':{},'result':{'enum':['match','no_match','unknown']},'evidence':array(evidence),'unusable_evidence':array(unusable)})
    record=obj({'id':TEXT,'values':values,'source_rows':array(source),'identities':obj({k:array(S) for k in ['email','contact_id','domain']}),
      'conflicts':{'type':'object','additionalProperties':{'type':'array'}},'problems':array(S),
      'qualification':obj({k:array(result) for k in ['required','preferences','exclusions']}),
      'fit_status':{'enum':['qualified','review','excluded']},'reasons':array(S),
      'suppression_matches':array({'type':'object'}),'contact_status':{'enum':['suppressed','missing_email','syntax_only','invalid_email']},
      'signals':array({'type':'object','required':['signal_id','priority_status','age_days']}),
      'priority':obj({'preference_matches':INTEGER,'fresh_signal_count':INTEGER,'latest_signal':{'type':['string','null']},'rank':{'type':['integer','null'],'minimum':1}}),
      'draft_blockers':array(S)})
    draft=obj({'record_id':TEXT,'email':TEXT,'status':{'const':'draft_for_review'},'subject':TEXT,'first':TEXT,'follow_up':TEXT,
      'claim_sources':obj({'prospect':array(TEXT),'offer':TEXT,'proof':TEXT})})
    run=obj({'schema_version':{'const':'1.0'},'engine_version':TEXT,'name':TEXT,'as_of':DATE,
      'input_sha256':obj({k:{'type':['string','null'],'pattern':'^[0-9a-f]{64}$'} for k in ['prospects','brief','signals','suppressions']}),
      'configuration':brief,'disclosures':array(TEXT),'summary':obj({k:INTEGER for k in ['input_rows','unique_records','duplicate_rows','qualified','review','excluded','suppressed','drafts']}),
      'records':array(record),'drafts':array(draft)})
    save('run',run)
    save('prospect-row',{'type':'object','properties':{k:S for k in FIELDS},'additionalProperties':S})
    save('signal-row',obj({k:S for k in ['contact_id','email','domain','type','observed_at','source_ref']},extra=True))
    save('suppression-row',obj({'type':{'enum':['email','contact_id','domain']},'value':TEXT,'reason':TEXT},extra=True))

if __name__=='__main__':
    main()
