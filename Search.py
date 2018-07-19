#!/usr/bin/env python3.6

import os
import pickle
import subprocess
import html
print ("importing....")
from pathlib import PurePath
from os import environ
from forms import SearchForm
from hyputils.hypothesis import HypothesisUtils, HypothesisAnnotation, HypothesisHelper, Memoizer, idFromShareLink, shareLinkFromId
from flask import Flask
from flask import (
    Blueprint, flash, g, redirect, render_template, request, session, url_for
)
from werkzeug.security import check_password_hash, generate_password_hash
from IPython import embed
from wtforms import Form, StringField, SelectField
bp = Blueprint('Search', __name__)

api_token = environ.get('RRIDBOT_API_TOKEN', 'TOKEN')  # Hypothesis API token
username = environ.get('RRIDBOT_USERNAME', 'USERNAME') # Hypothesis username
group = environ.get('RRIDBOT_GROUP', '__world__')
group_staging = environ.get('RRIDBOT_GROUP_STAGING', '__world__')
print(api_token, username, group)  # sanity check

READ_ONLY = True
if group_staging == '__world__' and not READ_ONLY:
    raise IOError('WARNING YOU ARE DOING THIS FOR REAL PLEASE COMMENT OUT THIS LINE')

#memfile = '/tmp/real-scibot-annotations.pickle'
if group.startswith('5'):
    print('Real annos')
    memfile = '/tmp/real-scibot-annotations.pickle'
elif group.startswith('4'):
    print('Test annos')
    memfile = '/tmp/test-scibot-annotations.pickle'

get_annos = Memoizer(memfile, api_token, username, group, 200000)

class Dashboard1(HypothesisHelper):
    def __repr__(self, depth=0):
        out = super().__repr__(depth=depth)
        return 'MODIFIED<br>\n' + out

def route(route_name):
    def wrapper(function):
        def inner(*args, **kwargs):
            print(route_name)
            return function(*args, **kwargs)
        return inner
    return wrapper

def make_app(annos):
    app = Flask('scibot dashboard')
    #hh = hh[0:80000]
    Annos = annos
    Annos.sort(key=lambda x: x.updated, reverse=True)
    hh = [Dashboard1(a, Annos) for a in Annos]
    base_url = '/dashboard/'
    k = 0
    kList = []
    URLDict = {}
    for k in range(0, len(hh)):
        if BaseURL(Annos[k]) in URLDict.keys():
            URLDict[BaseURL(Annos[k])] += 1
        else:
            URLDict[BaseURL(Annos[k])] = 1
            kList.append(k)

    @app.route('/dashboard', methods=('GET', 'POST'))
    def route_base():
        if request.method == 'POST':
            if request.form['submit'] == 'Search':
                return redirect('/dashboard/anno-search')
            elif request.form['submit'] == 'List of Missing':
                return redirect('/dashboard/anno-missing')
            elif request.form['submit'] == 'List of Unresolved':
                return redirect('/dashboard/anno-unresolved')
            elif request.form['submit'] == 'List of Incorrect':
                return redirect('/dashboard/anno-incorrect')
            elif request.form['submit'] == 'Papers with no Annos':
                return redirect('/dashboard/no-annos')
            elif request.form['submit'] == 'Journals':
                return redirect('/dashboard/Journals')
            elif request.form['submit'] == 'All Problems':
                return redirect('/dashboard/table')
            elif request.form['submit'] == 'Refresh Missing':
                file = open("missing.txt", "w")
                file.write("")
                file.close()
                return render_template('main.html')
            elif request.form['submit'] == 'Refresh Unresolved':
                file = open("unresolved.txt", "w")
                file.write("")
                file.close()
                return render_template('main.html')
            elif request.form['submit'] == 'Refresh Paper List':
                file = open("papers.txt", "w")
                file.write("")
                file.close()
                return render_template('main.html')
            elif request.form['submit'] == 'Refresh Incorrect':
                file = open("incorrect.txt", "w")
                file.write("")
                file.close()
                return render_template('main.html')
            elif request.form['submit'] == 'Refresh No PMID List':
                file = open("no-pmid.txt", "w")
                file.write("")
                file.close()
                return render_template('main.html')
            elif request.form['submit'] == 'Refresh No Annos':
                file = open("no-annos.txt", "w")
                file.write("")
                file.close()
                return render_template('main.html')
            elif request.form['submit'] == 'Refresh Journals':
                file = open("Journals.txt", "w")
                file.write("")
                file.close()
                return render_template('main.html')
            elif request.form['submit'] == 'Refresh Problems':
                file = open("table.txt", "w")
                file.write("")
                file.close()
                return render_template('main.html')
            elif request.form['submit'] == 'Paper List':
                return redirect('/dashboard/paper-list')
            elif request.form['submit'] == 'Papers with no PMID':
                return redirect('/dashboard/no-pmid')
        else:
            return render_template('main.html')

    @app.route('/dashboard/anno-count')
    def route_anno_count():
        return str(len(Annos))

    #@app.route(PurePath(base_url, 'anno-tags').as_posix())
    @app.route('/dashboard/anno-user/<user>')
    def route_anno_tags(user):
        print(user)
        out = '\n'.join([f'{anno.user} {anno.text} {anno.tags}<br>' for anno in Annos if anno.user == user])
        #embed()
        return out

    @app.route('/dashboard/anno-zero-pretty')
    def route_anno_zero_pretty():
        return repr(hh[0])

    @app.route('/dashboard/refresh')
    def route_refresh():
        annos = get_annos()
        return redirect('/dashboard')

    @app.route('/dashboard/Journals')
    def route_Journals():
        file = open("Journals.txt","r")
        paperStr = file.read()
        file.close()
        if paperStr == '':
            h = 0
            URLList = []
            counter = 0
            paperStr = str(counter) + ' Results:<br><br>'
            print("PROSSESING")
            for h in range(0, len(hh)):
                journal = Journal(annos[h])
                if "urn:x-pdf" in journal or "file:" in journal:
                    URLList.append(journal)
                if journal == "":
                    print (hh[h].shareLink)
                if not journal in URLList:
                    paperStr += "<br> <a href=" + hh[h].shareLink + "> Journal Link </a><br>"
                    paperStr += journal
                    counter += 1
                    URLList.append(journal)
            paperStr = str(counter) + paperStr[1:]
            file = open("Journals.txt", "w")
            file.write(paperStr)
            file.close()
        return (paperStr)	

    @app.route('/dashboard/DOI')
    def route_DOI():
        DOIStr = ""
        DOIList = []
        counter = 0
        for h in range(0, len(hh)):
            if [t for t in hh[h].tags if t.startswith("DOI")]:
                DOI = str([t for t in hh[h].tags if t.startswith("DOI")]).replace("DOI:", "")
                if not DOI in DOIList:
                    DOIStr += '<br> Anno #:%s <br>' % h
                    DOIStr += '<a href=' + hh[h].shareLink + '> Anno Link </a><br>'
                    DOIStr += DOI
                    counter += 1
                    if not DOI == '':
                        DOIList.append(DOI)
        return (str(counter) + "<br><br>" + DOIStr)
    @app.route('/dashboard/no-pmid')
    def route_no_PMID():
        file = open("no-pmid.txt","r")
        paperStr = file.read()
        file.close()
        if paperStr == '':
            h = 0
            URLList = []
            URLsUsed = []
            DOIDict = {}
            URLwDOI = {}
            PMIDDict = {}
            counter = 0
            URLList.append('curation.scicrunch.com/paper/2')
            URLList.append('curation.scicrunch.com/paper/1')
            URLList.append('scicrunch.org/resources')
            for a in range(0, len(hh)):
                URL = BaseURL(Annos[a])
                if URLDict[URL] < 3:
                    URLList.append(URL)
            paperStr = str(counter) + ' Results:<br><br>'
            print("PROSSESING")
            for h in range(0, len(hh)):
                if [t for t in hh[h].tags if t.startswith("DOI")]:
                    URL = BaseURL(Annos[h])
                    if not URL in URLsUsed:
                        DOI = str([t for t in hh[h].tags if t.startswith("DOI")]).replace("DOI:", "")
                        if not DOI in DOIDict.keys():
                            DOIDict[DOI] = []
                        DOIDict[DOI].append(URL)
                        URLwDOI[URL] = DOI
                        URLsUsed.append(URL)
            for h in range(0, len(hh)):
                k = 0
                URL = BaseURL(Annos[h])
                if [t for t in hh[h].tags if t.startswith("PMID")]:
                    PMID = str([t for t in hh[h].tags if t.startswith("PMID")]).replace("PMID:", "")
                    if URL in URLsUsed:
                        for k in range(0, len(DOIDict[URLwDOI[URL]])):
                            URLList.append(DOIDict[URLwDOI[URL]][k])
                    else:
                        URLList.append(URL)
                
            for h in range(0, len(hh)):
                URL = BaseURL(Annos[h])
                if not URL in URLList:
                    #if counter < 30:
                    paperStr += '<br> Anno #:%s <br>' % h
                    paperStr += '<a href=' + hh[h].shareLink + '> Anno Link </a><br>'
                    paperStr += repr(hh[h])
                    paperStr += "<br>" + URL
                    counter += 1
                    URLList.append(URL)
            paperStr = str(counter) + paperStr[1:]
            file = open("no-pmid.txt", "w")
            file.write(paperStr)
            file.close()
        return (paperStr)

    @app.route('/dashboard/table')
    def route_table():
        file = open("table.txt")
        returnStr = file.read()
        file.close()
        if returnStr == '':
            h = 0
            a = 0 
            counter = 0
            returnStr += """0 Problems:
<html>
<style type="text/css">
  td {width: 300px; hight 40px}     
  td {border: 1px solid #000000;}
</style>
<table cellpadding = 3 cellspacing = 0>
<tr>
  <td width: 70px>#</td>
  <td>Problem</th>
  <td>PMID</th>
  <td>Link</th>
  <td>Annotated By</th>
  <td>Notes</th>
</tr>
"""
            URLList = []
            URLsUsed = []
            DOIDict = {}
            URLwDOI = {}
            PMIDDict = {}
            URLList.append('curation.scicrunch.com/paper/2')
            URLList.append('curation.scicrunch.com/paper/1')
            URLList.append('scicrunch.org/resources')
            for a in range(0, len(hh)):
                URL = BaseURL(Annos[a])
                if URLDict[URL] < 3:
                    PMIDDict[URL] = "<a href=https://www.ncbi.nlm.nih.gov/pubmed/> PubMed </a>"
            print("PROSSESING")
            for h in range(0, len(hh)):
                if [t for t in hh[h].tags if t.startswith("DOI")]:
                    URL = BaseURL(Annos[h])
                    if not URL in URLsUsed:
                        DOI = str([t for t in hh[h].tags if t.startswith("DOI")]).replace("DOI:", "")
                        if not DOI in DOIDict.keys():
                            DOIDict[DOI] = []
                        DOIDict[DOI].append(URL)
                        URLwDOI[URL] = DOI
                        URLsUsed.append(URL)
            for h in range(0, len(hh)):
                k = 0
                URL = BaseURL(Annos[h])
                if [t for t in hh[h].tags if t.startswith("PMID")]:
                    PMID = str([t for t in hh[h].tags if t.startswith("PMID")]).replace("PMID:", "")
                    if URL in URLsUsed:
                        for k in range(0, len(DOIDict[URLwDOI[URL]])):
                                PMIDDict[DOIDict[URLwDOI[URL]][k]] = PMID
                    else:
                        PMIDDict[URL] = PMID
            for h in range(0, len(hh)):
                URL = BaseURL(Annos[h])
                if URL in PMIDDict.keys():
                    PMID = PMIDDict[URL]
                elif not URL in URLList:
                    counter += 1
                    PMID = "<a href=https://www.ncbi.nlm.nih.gov/pubmed/> PubMed </a>"
                    returnStr += "<tr><td>"+str(counter)+"</td><td>NO PMID</td><td>"+ PMID +"</td><td><a href=" + Annos[h].uri + "> Paper Link </a></td><td>"+Annos[h].user+"</td><td>""</td></tr>"
                    URLList.append(URL)
                if [t for t in hh[h].tags if "Missing" in t and not "NoFurtherAction" in t and len(hh[h].tags) == 1]:
                    counter += 1
                    returnStr += "<tr><td>"+str(counter)+"</td><td>MISSING</td><td>"+ PMID +"</td><td><a href=" + hh[h].shareLink + "> Anno Link </a></td><td>"+Annos[h].user+"</td><td>"+hh[h].text+"</td></tr>"
                if [t for t in hh[h].tags if "Incorrect" in t and not "NoFurtherAction" in t and len(hh[h].tags) == 1]:
                    counter += 1
                    returnStr += "<tr><td>"+str(counter)+"</td><td>INCORRECT</td><td>"+ PMID +"</td><td><a href=" + hh[h].shareLink + "> Anno Link </a></td><td>"+Annos[h].user+"</td><td>"+hh[h].text+"</td></tr>"
                if [t for t in hh[h].tags if "Unresolved" in t and not "NoFurtherAction" in t and len(hh[h].tags) == 1]:
                    counter += 1
                    returnStr += "<tr><td>"+str(counter)+"</td><td>UNRESOLVED</td><td>"+ PMID +"</td><td><a href=" + hh[h].shareLink + "> Anno Link </a></td><td>"+Annos[h].user+"</td><td>"+hh[h].text+"</td></tr>"
            returnStr += "</table></html>"
            returnStr = str(counter) + returnStr[1:]
            file = open("table.txt", "w")
            file.write(returnStr)
            file.close()
        return(returnStr)
    @app.route('/dashboard/no-annos')
    def route_No_Annos():
        file = open("no-annos.txt","r")
        annoStr = file.read()
        file.close()
        if annoStr == '':
            h = 0
            counter = 0
            annoStr += str(counter) + ' Results:<br>'
            print("PROSSESING")
            for a in range(0, len(URLDict)):
                if URLDict[BaseURL(Annos[kList[a]])] < 3:
                    annoStr += '<br> Anno #:%s <br>' % kList[a]
                    annoStr += '<a href=' + hh[kList[a]].shareLink + '> Anno Link </a><br>'
                    annoStr += repr(hh[kList[a]])
                    annoStr += BaseURL(Annos[kList[a]])
                    counter += 1
            annoStr = str(counter) + annoStr[1:]
            file = open("no-annos.txt", "w")
            file.write(annoStr)
            file.close()
            return (annoStr)
        else:	
            return annoStr


    @app.route('/dashboard/paper-list')
    def route_Paper_List():
        file = open("papers.txt","r")
        paperStr = file.read()
        file.close()
        if paperStr == '':
            h = 0
            a = 0
            PMIDList = []
            DOIList = []
            URLList = []
            URLList.append('curation.scicrunch.com/paper/2')
            URLList.append('curation.scicrunch.com/paper/1')
            URLList.append('scicrunch.org/resources')
            for a in range(0, len(hh)):
                URL = BaseURL(Annos[a])
                if URLDict[URL] < 3:
                    URLList.append(URL)
            counter = 0
            ProbCounter = 0
            paperStr += str(counter) + ' Results:<br>' + str(ProbCounter) + ' Papers with no PMID or DOI<br><br>'
            print("PROSSESING")
            for h in range(0, len(hh)):
                if [t for t in hh[h].tags if t.startswith("DOI")]:
                    DOI = str([t for t in hh[h].tags if t.startswith("DOI")]).replace("DOI:", "")
                    URL = BaseURL(Annos[h])
                    if not DOI in DOIList and not URL in URLList:
                        paperStr += '<br> Anno #:%s <br>' % h
                        paperStr += '<a href=' + hh[h].shareLink + '> Anno Link </a><br>'
                        paperStr += repr(hh[h])
                        paperStr += URL
                        counter += 1
                        if not DOI == '':
                            DOIList.append(DOI)
                        URLList.append(URL)
                    elif not DOI in DOIList:
                        if not DOI == '':
                            DOIList.append(DOI)
                    elif not URL in URLList:
                        URLList.append(URL)
                if [t for t in hh[h].tags if t.startswith("PMID")]:
                    PMID = str([t for t in hh[h].tags if t.startswith("PMID")]).replace('PMID:', '')
                    URL = BaseURL(Annos[h])
                    if not PMID in PMIDList and not URL in URLList:
                        paperStr += '<br> Anno #:%s <br>' % h
                        paperStr += '<a href=' + hh[h].shareLink + '> Anno Link </a><br>'
                        paperStr += repr(hh[h])
                        paperStr += URL
                        counter += 1
                        if not PMID == '':
                            PMIDList.append(PMID)
                        URLList.append(URL)
                    elif not PMID in PMIDList:
                        if not PMID == '':
                            PMIDList.append(PMID)
                    elif not URL in URLList:
                        URLList.append(URL)
            for h in range(0, len(hh)):
                URL = BaseURL(Annos[h])
                if not URL in URLList:
                    paperStr += '<br> Anno #:%s <br>' % h
                    paperStr += '<a href=' + hh[h].shareLink + '> Anno Link </a><br>'
                    paperStr += '<span	style="color:red">NO PMID OR DOI</span><br>'
                    paperStr += repr(hh[h])
                    paperStr += URL
                    counter += 1
                    ProbCounter += 1
                    URLList.append(URL)
            paperStr = str(counter) + paperStr[1:14] + str(ProbCounter) + paperStr[15:]
            file = open("papers.txt", "w")
            file.write(paperStr)
            file.close()
            return (paperStr)
        else:	
            return paperStr

    @app.route('/dashboard/anno-incorrect')
    def route_anno_incorrect():
        file = open("incorrect.txt","r")
        incorrectStr = file.read()
        file.close()
        if incorrectStr == '':
            h = 0
            counter = 0
            incorrectStr += str(counter) + ' Results:<br><br>'
            print("PROSSESING")
            for h in range(0, len(hh)):
                if "RRIDCUR:Incorrect" in hh[h].tags and len(hh[h].tags) == 1:
                    incorrectStr += '<br> Anno #:%s <br>' % h
                    incorrectStr += '<a href=' + hh[h].shareLink + '> Anno Link </a><br>'
                    incorrectStr += repr(hh[h])
                    counter += 1
            incorrectStr = str(counter) + incorrectStr[1:]
            file = open("incorrect.txt", "w")
            file.write(incorrectStr)
            file.close()
            return (incorrectStr)
        else:	
            return incorrectStr

    @app.route('/dashboard/anno-unresolved')
    def route_anno_unresolved():
        file = open("unresolved.txt","r")
        unresolvedStr = file.read()
        file.close()
        if unresolvedStr == '':
            h = 0
            counter = 0
            unresolvedStr += str(counter) + ' Results:<br><br>'
            print("PROSSESING")
            for h in range(0, len(hh)):
                if "RRIDCUR:Unresolved" in hh[h].tags and len(hh[h].tags) == 1:
                    unresolvedStr += '<br> Anno #:%s <br>' % h
                    unresolvedStr += '<a href=' + hh[h].shareLink + '> Anno Link </a><br>'
                    unresolvedStr += repr(hh[h])
                    counter += 1
            unresolvedStr = str(counter) + unresolvedStr[1:]
            file = open("unresolved.txt", "w")
            file.write(unresolvedStr)
            file.close()
            return (unresolvedStr)
        else:	
            return unresolvedStr

    @app.route('/dashboard/results')
    def search_results(search):
        h = 0
        hlist = []
        hstr = ''
        counter = 0
    #    if search.data['search'] == '':
    #        h = 0
    #        hstr = ''
    #        for h in range(0, len(hh)):
    #            hstr += repr(hh[h])
    #            h += 1
    #        return(hstr)
    #    else:
        if search.data['select'] == 'ID':
            for h in range(0, len(hh)):
                if search.data['search'] in hh[h].id:
                    hstr += '<br> Anno #:%s <br>' % h
                    hstr += '<a href=' + hh[h].shareLink + '> Anno Link </a><br>'
                    hstr += repr(hh[h])
                    counter += 1
            if hstr == '':
                return('no results')
            return (str(counter) + ' Results:<br><br>' + hstr)
            #return render_template('results.html', results=html.unescape(hstr))
        elif search.data['select'] == 'Tags':
            for h in range(0, len(hh)):
                if [t for t in hh[h].tags if search.data['search'] in t]:
                    hstr += '<br> Anno #:%s <br>' % h
                    hstr += '<a href=' + hh[h].shareLink + '> Anno Link </a><br>'
                    hstr += repr(hh[h])
                    counter += 1
            if hstr == '':
                return('no results')
            print (str(len(hlist)))
            print (len(hh))
            return (str(counter) + ' Results:<br><br>' + hstr)
            #return render_template('results.html', results=hstr)
        elif search.data['select'] == 'User':
            for h in range(0, len(hh)):
                if Annos[h].user == search.data['search']:
                    hstr += '<br> Anno #:%s <br>' % h
                    hstr += '<a href=' + hh[h].shareLink + '> Anno Link </a><br>'
                    hstr += repr(hh[h])
                    counter += 1
            if hstr == '':
                return('no results')
            return (str(counter) + ' Results:<br><br>' + hstr)
        else:
            return search_text(search.data['select'], Annos, hh, search.data['search'])

    @app.route('/dashboard/anno-search', methods=('GET', 'POST'))
    def route_anno_search():
        search = SearchForm(request.form)
        if request.method == 'POST':
            return search_results(search)
        return render_template('search.html', form=search)

    @app.route('/dashboard/anno-missing', methods=('GET', 'POST'))
    def route_anno_missing():
        file = open("missing.txt","r")
        missingStr = file.read()
        file.close()
        if missingStr == '':
            h = 0
            counter = 0
            missingStr += str(counter) + ' Results:<br><br>'
            print("PROSSESING")
            for h in range(0, len(hh)):
                if "RRIDCUR:Missing" in hh[h].tags and len(hh[h].tags) == 1:
                    missingStr += '<br> Anno #:%s <br>' % h
                    missingStr += '<a href=' + hh[h].shareLink + '> Anno Link </a><br>'
                    missingStr += repr(hh[h])
                    counter += 1
            missingStr = str(counter) + missingStr[1:]
            file = open("missing.txt", "w")
            file.write(missingStr)
            file.close()
            return (missingStr)
        else:	
            return missingStr
    

    #new_function = route('/my/route')(route_base)

    #return new_function
    return app
    #new_function_outside = make_app('not really annos')
def search_text(text, annos, hh, search):
        h = 0
        hlist = []
        hstr = ''
        counter = 0
        for h in range(0, len(hh)):
            hsplit = hh[h].text.split('<p>',hh[h].text.count('<p>'))
            t = 0
            Data = ''
            for t in range(0, len(hsplit)):
                if text in hsplit[t]:
                    Data = hsplit[t].replace(text + ': ', '')
            
            if search.upper() in Data.upper():
                hstr += '<br> Anno #:%s <br>' % h
                hstr += '<a href=' + hh[h].shareLink + '> Anno Link </a><br>'
                hstr += repr(hh[h])
                hstr += "<br>" + BaseURL(annos[h])
                counter += 1
        if hstr == '':
            return('no results')
        return (str(counter) + ' Results:<br><br>' + hstr)

def BaseURL(anno):
    URL = anno.uri.replace(".long", "").replace("/abstract", "").replace("/full","").replace(".short", "").replace(".full", "").replace("http://","").replace("https://","").replace("/FullText","").replace("/Abstract","").replace("/enhanced","")
    SplitURL = URL.split("/", URL.count("/"))
    if len(SplitURL) == 1:
        print(URL)
    if SplitURL[-1] == '':
        URL = SplitURL[0] + SplitURL[-2]
    else:
        URL = SplitURL[0] + SplitURL[-1]
    return URL

def Journal(anno):
    URL = anno.uri.replace(".long", "").replace("/abstract", "").replace("/full","").replace(".short", "").replace(".full", "").replace("http://","").replace("https://","").replace("/FullText","").replace("/Abstract","").replace("/enhanced","")
    SplitURL = URL.split("/", URL.count("/"))
    if len(SplitURL) == 1 or len(SplitURL) == 0:
        print(URL)
    URL = SplitURL[0]
    return URL

def main():
    annos = get_annos()
    app = make_app(annos)
    app.secret_key = 'super secret key'
    app.config['SESSION_TYPE'] = 'filesystem'
    print(app.view_functions)
    app.debug = True
    app.run(host='localhost', port=8080)
    #embed()

if __name__ == '__main__':
    main()