from django.shortcuts import render
from django.http import HttpResponse
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage, InvalidPage
import sys
import json
sys.path.append('../')
import globalvar as gl
import jaydebeapi, os


def home(request):
	attributes=gl.get_value("attributes")
	annotated_entities=gl.get_value("annotated_entities")
	return render(request,'home.html',{'List': json.dumps(annotated_entities),'attributes': json.dumps(attributes)})

# collapsible trees
def tree(request):
	snomed_concepts=gl.get_value("snowmed_concepts")
	return render(request,'tree_view.html',{'Dict': json.dumps(snomed_concepts)})

def collocation_cui(request):
	return render(request,'collocation_cui.html')

def collocation_snomed(request):
	return render(request,'collocation_snomed.html')

def snomed_hierarchy(request):
	with open("/static/data/snomed_hierarchy.json", 'r') as f:
		snomed_concepts = json.load(f)
		return render(request,'snomed_hierarchy.html',{'Dict': json.dumps(snomed_concepts)})

def snomed_three_layer_tree(request):
	with open(".\\static\\data\\snomed_hierarchy_three_layer_tree.json", 'r') as f:
		snomed_concepts = json.load(f)
		return render(request,'snomed_hierarchy.html',{'Dict': json.dumps(snomed_concepts)})

def snomed_four_layer_tree(request):
	with open(".\\static\\data\\snomed_hierarchy_four_layer_tree.json", 'r') as f:
		snomed_concepts = json.load(f)
		return render(request,'snomed_hierarchy.html',{'Dict': json.dumps(snomed_concepts)})
def frequent_itemset(request):
    frequent_itemset=gl.get_value("frequent_itemset")
    return render(request,'frequent_item.html',{'List': json.dumps(frequent_itemset)})
def tf_idf(request):
    tf_idf=gl.get_value("tf_idf")
    data=[]
    for key, value in tf_idf.items():
        concept=value['concept']
        tfidf=value["value"]
        name=concept+" ("+key+") "+str(tfidf)
        node={"name":name}
        data.append(node)

    return render(request,'tf_idf.html',{'List': json.dumps(data)})

@csrf_exempt
def paginator_view(request):
    result=gl.get_value("search_result")['docs']
    total_num=min(len(result),100)
    pages_amount=min(int(len(result)/10+1),10)
    essays={}
    essays['range']=list(range(1,pages_amount+1))
    
    if request.method == "GET":
       
        essays['has_previous']=None
        essays['page']=1
        if total_num>1:
            essays['has_next']=True
            essays['content']=result[:10]
        else:
            essays['has_next']=None
            essays['content']=result

        return render(request, 'page.html', {'essays': essays,'num':total_num})

    else:
     
         page = int(request.POST.get('page'))
         essays['page']=page
         if  pages_amount>page:
             essays['has_next']=True
         else:
             essays['has_next']=False

         if  pages_amount>1 and page>1:
             essays['has_previous']=True
         else:
             essays['has_previous']=False


         start=(page-1)*10
         if page==total_num:
            essays['content']=result[start:]
         else:
            
            essays['content']=result[start:start+10]
        
        
         
         return JsonResponse(json.dumps({"essays" : essays}),safe=False)

	