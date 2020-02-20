# coding: utf-8
from flask import Flask, render_template, request, jsonify
# Blueprintはpagenateのため
from flask_paginate import Pagination, get_page_parameter
import csv
import urllib.parse
import urllib.request
import json
import re
app = Flask(__name__)
app.config['JSON_AS_ASCII'] = False

def get_col(proj):
   solr_url = 'http://localhost:8983/solr/minhon/select?'
   solr_url = solr_url + 'fl=collection_st&q=*&group=true&group.field=collection_st'
   if proj != 'すべて':
      solr_url = solr_url +'&fq=project:"'+urllib.parse.quote(proj)+'"'
   req = urllib.request.Request(solr_url)
   res = urllib.request.urlopen(req)
   array_body = json.loads(res.read().decode('utf-8'))
   array_group = array_body['grouped']['collection_st']['groups']
   array_col = {}
   for egroup in array_group:
      enum = egroup['doclist']['numFound']
      collection = egroup['doclist']['docs'][0]['collection_st']
      array_col[collection] = enum
   return (array_col)

def get_proj():
   solr_url = 'http://localhost:8983/solr/minhon/select?'
   solr_url = solr_url + 'fl=project_st&q=*&group=true&group.field=project_st'
   req = urllib.request.Request(solr_url)
   res = urllib.request.urlopen(req)
   array_body = json.loads(res.read().decode('utf-8'))
   array_group = array_body['grouped']['project_st']['groups']
   array_proj = {}
   for egroup in array_group:
      enum = egroup['doclist']['numFound']
      project = egroup['doclist']['docs'][0]['project_st']
      array_proj[project] = enum
   return (array_proj)

@app.route('/get_list/')
def hello3():
#/get_list/?type=proj&name=
   get_type = request.args.get('type', '')
   get_name = request.args.get('name', '')
   if get_type == 'proj':
      return jsonify(get_col(get_name))   

@app.route('/search/')
def hello():
   debug_url = ''
   array = []
   array_docs = {}
   per_page_org = 10
   sch_key = request.args.get('url_key', '')
   sch_var = request.args.get('url_var', '')
   sch_proj = request.args.get('url_proj', '')
   sch_col = request.args.get('url_col', '')
   sch_entid = request.args.get('url_entid', '')   
   page = request.args.get(get_page_parameter(), type=int, default=1)
   startrow = (page - 1) * per_page_org
   if sch_var == "1":
      sch_obj = 'textConn'
   else:
      sch_obj = 'textNoKT'
   url_enc_key = '"'+urllib.parse.quote(sch_key, safe='~')+'"'
   sch_title  = request.args.get('url_title', '')
   solr_url = 'http://localhost:8983/solr/minhon/select?'
   solr_url = solr_url + 'hl=true&hl.fragsize=50&rows='+str(per_page_org)+'&hl.snippets=100&hl.fl='+sch_obj+'&start='+str(startrow)+'&'
   solr_url = solr_url + 'q='+sch_obj+':'
   #%E4%BD%9B
   solr_url = solr_url + url_enc_key
   if sch_entid != '':
      solr_url = solr_url + '%20AND%20entryID:'+sch_entid
   if sch_col != 'すべて':
      solr_url = solr_url+'%20AND%20collection:"'+urllib.parse.quote(sch_col)+'"'
   if sch_proj != 'すべて':
      solr_url = solr_url+'%20AND%20project:"'+urllib.parse.quote(sch_proj)+'"'
   solr_url = solr_url+'&facet.pivot=project_st,collection_st,entryID,entry_st&facet=on&facet.sort=count'
   pr_sch_key = sch_key
   pr_sch_col = sch_col
   pr_sch_proj = sch_proj
#   req = urllib.request.Request(solr_url)
#   res = urllib.request.urlopen(req)
   res = urllib.request.urlopen(solr_url)
   array_body = json.loads(res.read().decode('utf-8'))
   for edoc in array_body['response']['docs']:
      obj_id = edoc['id']
      ent = edoc['entry']
      imgf = edoc['imageID']
      imgt = edoc['imageThumb']
      ent_id = edoc['entryID']
      ent_num = re.sub(r'[\[\]]','',str(edoc['folio']))
#      ent_num = edoc['folio']
      array_docs[obj_id] = [ent, imgf, imgt, ent_id, ent_num]
   array_col = get_col(sch_proj)
   array_proj = get_proj()
   array_hls = array_body['highlighting']
   array_hls2 = {}
   hit_key = array_body['response']['numFound']
#  hit_key = solr_url
   pagination = Pagination(page=page, total=hit_key,  per_page=per_page_org, css_framework='bootstrap4')
   for pageid,hitlines in array_hls.items():
      list_lines = hitlines[sch_obj]
      array_hls2[pageid] = {}
      array_hls2[pageid]['hitcontent'] = list_lines
#   debug_url = solr_url
   ar_entry_st = array_body['facet_counts']['facet_pivot']['project_st,collection_st,entryID,entry_st']
   en = 0
   res_ent_list = {}
   templ_ent_list = []
   for ar_proj_st in ar_entry_st:
      f_proj_st = ar_proj_st['value']
      f_proj_num = ar_proj_st['count']      
      if 'pivot' in ar_proj_st:
         for ar_coll_st in ar_proj_st['pivot']:
            f_coll_nm = ar_coll_st['value']
            f_coll_num = ar_coll_st['count']
            f_proj_text = f_proj_st+'/'+f_coll_nm
            proj_dict = {}
            proj_dict['proj'] = f_proj_text+' ('+str(f_coll_num)+')'
            proj_dict['projdata'] = []
            if 'pivot' in ar_coll_st:
               for ar_ent_id in ar_coll_st['pivot']:
                  f_ent_id = ar_ent_id['value']
                  f_ent_num = ar_ent_id['count']
                  if 'pivot' in ar_ent_id:
                     for ar_ent_st in ar_ent_id['pivot']:
                        f_ent_st = ar_ent_st['value']
                        f_ent_num = ar_ent_st['count']
                        f_ent_text = f_ent_st+' ('+str(f_ent_num)+')'
                        f_ent_key = '&url_entst='+f_ent_st+'&url_entid='+f_ent_id
                        templ_ent = {}
                        templ_ent['uval'] = 'url_key='+sch_key+'&url_var='+sch_var+'&url_proj='+sch_proj+'&url_col='+sch_col+f_ent_key
                        templ_ent['nm']= f_ent_text
                        proj_dict['projdata'].append(templ_ent)
            templ_ent_list.append(proj_dict)
   
   entry_menu = ''# ar_entry_st
   if len(templ_ent_list) > 0:
      entry_menu = '資料単位で絞り込み:'
#   debug_url = templ_ent_list
   html = render_template('index.html', navigation = array_hls2, docs = array_docs, col_list = array_col, sch_key = pr_sch_key, pr_sch_var=sch_var, pr_sch_col = pr_sch_col, hit_key = hit_key, row = res, pagination = pagination, pr_sch_proj = pr_sch_proj, proj_list = array_proj, debug_url = debug_url, entry_list=templ_ent_list, entry_menu = entry_menu)
   return html
#    return uname

@app.route('/')
def hello2():
   array_col = get_col('すべて')
   array_proj = get_proj()
   pr_sch_proj = 'すべて'
   pr_sch_col = 'すべて'
   html = render_template('index.html', col_list = array_col, pagination = '', proj_list = array_proj, pr_sch_col= pr_sch_col, pr_sch_proj = pr_sch_proj)
   return html

if __name__ == "__main__":
    app.run(debug=True)

