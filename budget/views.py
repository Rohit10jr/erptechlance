from django.db import reset_queries
from rest_framework.views import APIView
from rest_framework.response import Response
from .models import *
# from Company.models import user_company
# from Company.models import user_group
import jwt
from django.http import JsonResponse
from .serializers import *
from company.models import *
from User.models import User, transaction_right, user_group, user_right
from datetime import date, timedelta
from django.http.response import HttpResponse
import PIL
import json
from decimal import Decimal as D


def verify_token(request):
    try:
        if not (request.headers['Authorization'] == "null"):
            token = request.headers['Authorization']
    except:
        if not (request.COOKIES.egt("token") == "null"):
            token = request.COOKIES.get('token')
    
    else:
        context = {
            "success": False,
            "mesage":"INVALID_TOKEN",
        }

        payload = JsonResponse(context)

    try:
        payload = jwt.decode(token, 'secret', algorithm=['HS256'])
    except:
        context =  {
            "success":False,
            "message": "INVALID_TOKEN"
        }

        payload = JsonResponse(context)
    return payload


def get_error(serializerErr):
    err = ''
    for i in serializerErr:
        err = serializerErr[i][0]
        break
    return err

def check_user_company_right(transaction_rights, user_company_id, user_id, need_right):
    try:
        # Query-1 : obtain Transaction Right
        check_transaction_right = transaction_right.objects.filter(transactions=transaction_rights)[0].id
        # Query-2 : Obtain Group id from user company
        check_user_group = user_company.objects.get(user=user_id, company_master_id=user_company_id).user_group_id.id
        # find instance of Query-1 and Query-2
        transaction_right_instance = transaction_right.objects.get(id=check_transaction_right)
        user_group_instance = user_group.objects.get(id=check_user_group)
        # Query-3 : check user right 
        check_user_right = user_right.objects.get(user_group_id=user_group_instance, transaction_id=transaction_right_instance)
    except:
        return False
    
    if need_right =="can_create":
        return check_user_right.can_create
    elif need_right == "can_alter":
        return check_user_right.can_alter
    elif need_right == "can_delete":
        return check_user_right.can_delete
    else:
        return check_user_right.can_view
        


class CreateBudget(APIView):
    def post(self, request):
        payload = verify_token(request)
        try:
            user = User.objects.filter(id=payload['id']).first()
        except:
            return payload
        
        user_permission=False
        if request.data['budget_type']=='P&L':
            user_permission = check_user_company_right("Budget-P&L", request.data['company_master_id'], user.id, "can_create")
        elif request.data['budget_type'] == 'Cashflow':
            user_permission = check_user_company_right("Budget-Cash flow", request.data['company_master_id'], user.id, "can_create")

        
        if user_permission:
            serializer = BudgetSerializer(data= request.data)
            if not serializer.is_valid():
                return Response({
                    "success":False,
                    "message":get_error(serializer.errors),
                    "data":{
                        "email":user.email
                    }
                })
            company_name = company_master.objects.get(id=request.data['company_master_id']).company_name
            serializer.save()
            if request.data['budget_type']=='P&L':
                ledgers = []

                all_ledger_master = ledger_master.objects.filter(company_master_id=request.data['company_master_id'])
                for instance in all_ledger_master:
                    if instance.acc_group_id.acc_head_id.bs==False:
                        ledgers.append({'id':instance.id, 'ledger_id':instance.ledger_id})

                latest_budget = budget.objects.lastest('id')

                for i in ledgers:
                    new_budget_details = budget_details(budget_id_id=latest_budget.id,company_master_id_id=latest_budget.company_master_id.id,ledger_id_id = i['id'],
                    jan=0,feb=0,mar=0,apr=0,may=0,jun=0,jul=0,aug=0,sep=0,octo=0,nov=0,dec=0,created_by=user.email)
                    new_budget_details.save()
                    new_rev_budget_details = revised_budget_details(budget_id_id=latest_budget.id,company_master_id_id=latest_budget.company_master_id.id,ledger_id_id = i['id'],
                    jan=0,feb=0,mar=0,apr=0,may=0,jun=0,jul=0,aug=0,sep=0,octo=0,nov=0,dec=0,created_by=user.email)
                    new_rev_budget_details.save()
            
            return Response({
                "success":True,
                "message": "budget added to" + company_name + "successfully",
                "data": serializer.data
            })
        
        else:
            return Response({
                "success":False,
                "message":"Not allowed to add budget",
                "data":{
                    "email":user.email
                }
            })
        

class EditBudget(APIView):
    def put(self, request, id):
        payload = verify_token(request)
        try:
            user = User.objects.filter(d=payload['id']).first()
        except:
            return payload
        
        user_permission=False

        if int(request.data['authoriser']) == int(user.id):
            if request.data['budget_type']=='P&L':
                user_permission = check_user_company_right("Budget-P&L", request.data['company_master_id'], user.id, "can_edit")

            elif request.data['budget_type']=='Cashflow':
                user_permission = check_user_company_right("Budget-Cash flow", request.data['company_master_id'], user.id, "can_edit")

            if user_permission:
                budget_instance = budget.objects.get(id=id)
                serializer = BudgetSerializer(budget_instance, daat=request.data)
                if not serializer.is_valid():
                    return Response({
                        "success":False,
                        "message":get_error(serializer.errors),
                        "data":{
                            "email":user.email
                        }
                    })
                serializer.save()

                return Response({
                    "success":True,
                    "message":"budget has been edited successfully",
                    "data":serializer.data
                })
            
            else:
                return Response({
                    "succcess":False,
                    "message":"Not allowed to edit budget",
                    "data":{
                        "email":user.email
                    }
                })
            
    
class DeleteBudget(APIView):
    def delete(self, request, id):
        payload = verify_token(request)
        try:
            user = User.objects.filter(id=payload['id']).first()
        except:
            return payload
        user_permission=False
        if int(request.data['authoriser'])==int(user.id):
            if request.data['budget_type']=='P&L':
                user_permission = check_user_company_right("Budget-P&L", request.data['company_master_id'], user.id, "can_delete")
            elif request.data['budget_type']=='Cashflow':
                user_permission = check_user_company_right("Budget-Cash flow", request.data['company_master_id'], user.id, "can_delete")
        
        if user_permission:
            budget_instance = budget.objects.get(id=id)
            b_name = budget_instance.budget_name
            company_name = budget_instance.company_master_id.company_name
            budget_instance.delete()
            return Response({
                'success':True,
                'message': "Budget "+b_name+" for " + company_name + " has been removed",
            })
        
        else:

            return Response({
                'success':False,
                'message': 'you are not allowed to delete this budget'
            })
        

class GetBudget(APIView):
    def get(self, request, id):
        payload = verify_token(request)
        try:
            user=User.objects.filter(id=payload['id']).first()
        except:
            return payload
        
        user_permission = check_user_company_right("Budget-P&L", id, user.id, "can_view")
        if user_permission:
            budget_instance = budget.objects.filter(company_master_id=id)
            serializer = GetBudgetSerializer(budget_instance, many=True)
            return Response({
            'success': True,
            'message':'',
            'data': serializer.data
            })
        else:
            return Response({
                'success':False,
                'message':'You are not allowed to view budget',
                'data':[]
            })

    

class GetBudgetDetails(APIView):
    def get(self, request, id):
        payload = verify_token(request)
        try:
            user=User.objects.filter(id=payload['id']).first()
        except:
            return payload
        
        user_permission = False
        company_id = budget.objects.get(id=id).company_master_id.id 
        user_permission = check_user_company_right("Budget-P&L", company_id, user.id, "can_view")

        if user_permission:
            budget_instance = budget.objects.get(id=id)
            budget_serializer = GetBudgetSerializer(budget_instance)   

            budget_details_instances = budget_details.objects.filter(budget_id=id)
            serializer = GetBudgetDetailsSerializer(budget_details_instances, many=True)

            return Response({
            'success': True,
            'message':'',
            'budget':budget_serializer.data,
            'data': serializer.data
            })
        else:
            return Response({
                'success': False,
                'message': 'You are not allowed to view Budget details',
                'data': []
            })
        

class CreateBudgetDetails(APIView):
    def post(self, request):
        payload = verify_token(request)
        try:
            user = User.objects.filter(id=payload['id']).first()
        except:
            return payload
        
        user_permission = check_user_company_right("Budget-P&L", request.data['company_master_id'], user.id, "can_create")

        if user_permission:
            serializer = BudgetDetailsSerializer(data = request.data)
            if not serializer.is_valid():
                return Response({
                    "success":False,
                    "message":get_error(serializer.errors),
                    "data": {
                        "email":user.email
                    }
                })
            revised_serializer = RevisedBudgetDetailsSerializer(data = request.data)
            if not revised_serializer.is_valid():
                return Response({
                "success":False,
                "message":get_error(serializer.errors),
                "data": {
                    "email":user.email
                }
                })
            
            company_name = company_master.objects.get(id=request.data['company_master_id']).company_name
            serializer.save()
            revised_serializer.save()

            return Response({
                "success":True,
                "message":"Budget details added to "+company_name+" successfully",
                "data": serializer.data
                })
        else:
            return Response({
            "success":False,
            "message":"Not Allowed to add budget",
            "data": {
                    "email":user.email
                }
            })
        
        

class EditBudgetDetails(APIView):
    def put(self, request, id):
        payload = verify_token(request)
        try:
             user = User.objects.filter(id=payload['id']).first()
        except:
            return payload
        
        budget_instance = budget.objects.get(id=id)
        user_permission=False
        if budget_instance.authoriser.id==user.id:
            user_permission = check_user_company_right("Budget-P&L", request.data['company_master_id'], user.id, "can_edit")
        
        if user_permission:
            budget_details_instance = budget_details.objects.get(id=id)
            serializer = BudgetDetailsSerializer(budget_details_instance, data = request.data)
            if not serializer.is_valid():
                return Response({
                "success":False,
                "message":get_error(serializer.errors),
                "data": {
                    "email":user.email
                } 
                })
            
            serializer.save()
            
            return Response({
                "success":True,
                "message":"Budget details has been edited successfully",
                "data": serializer.data
                })
        else:
            return Response({
            "success":False,
            "message":"Not Allowed to edit this budget details",
            "data": {
                    "email":user.email
                }
            })