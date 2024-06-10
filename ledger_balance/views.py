from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from django.http import JsonResponse
from .serializers import LedgerBalanceSerializer, LedgerBalanceBillwiseSerializer, OpBalanceBrsSerializer, GetLedgerBalanceSerializer, GetOpBalanceBrsSerializer 
from datetime import date, timedelta
from django.http.response import HttpResponse
from .models import ledger_balance,op_bal_brs,ledger_bal_billwise
from company.models import ledger_master, user_company, year_master, company_master
from User.models import transaction_right, user_group, user_right, User
import jwt
from decimal import Decimal as D



def verify_token(request):
    try:
        if not (request.headers['Authorization'] == "null"):
            token = request.headers['Authorization'] 
    except:
        if not(request.COOKIES.get('token0')=="null"):
            token = request.COOKIES.get('token')
    
    else:
        context = {
            "succes":False,
            "message":"INVALID_TOKEN",
        }
        payload = JsonResponse(context)

    if not token:
        context = {
            "success":False,
            "message":"INVALID_TOKEN",
        }

        payload = JsonResponse(context)

    if not token:
        context = {
            "success":False, 
            "message":"INVALID_TOKEN",
        }
        payload = JsonResponse(context)

    try:
        payload = jwt.decode(token, 'secret', algorithm=['HS256'])

    except :
        context = {
                "success":False,
                "message":"INVALID_TOKEN",
            }
        payload =  JsonResponse(context)
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


class GetLedgerIdsWithBs(APIView):
    def get(self, request):
        payload = verify_token(request)
        try:
            user=  User.objects.filter(id=payload['id']).first()
        except:
            return payload
        
        ledgers = []

        all_ledger_master = ledger_master.objects.filter(company_master_id=id)
        for instance in all_ledger_master:
            if instance.acc_group_id.acc_head_id.bs==True:
                ledgers.append({'id':instance.id,'ledger_id':instance.ledger_id})


        return Response({
            'success':True,
            'message':'',
            'data':ledgers
        })
    

class AddLedgerBalance(APIView):
    def post(self, request):
        payload = verify_token(request)
        try:
            user = User.objects.filter(id=payload['id']).first()
        except:
            return payload
        
        user_permission = check_user_company_right("Opening Balance", request.data['company_master_id'], user.id, "can_create")
        if user_permission:
            year_master_instance = year_master.objects.get(company_master_id=request.data['company_master_id'], year_no=0)
            temp = request.data
            context = temp.dict()
            context['year_id'] = year_master_instance.id
            debit = 0
            credit = 0
            if context.get('dr'):
                debit = context.get('dr')
                context['fc_amount'] = request.data['fc_amount']
            if context.get('cr'):
                credit = context.get('cr')
                context['fc_amount'] = (-1)*D(request.data['fc_amount'])

            debit = D(debit)
            credit = D(credit)
            balance = debit - credit
            context['balance'] = balance
            if context['fc_amount'] == 0:
                fc_rate = "0"
            else:
                fc_rate = str(balance/D(context['fc_amount']))
            if fc_rate[0] == "-":
                fc_rate = fc_rate[1:]
            fc_rate = round(D(fc_rate), 4)

            context['fc_rate'] = fc_rate
            context['total_cr'] = D(credit)
            context['total_dr'] = D(Debit)
            serializer = LedgerBalanceBillwiseSerializer(data=context)

            if not serializer.is_valid():
                return Response({
                    "success":False,
                    "message": serializer.errors,
                })
            
            serializer.save()
            return Response({
                'success':False,
                'message':'YOU are not allowed to add ledger balance'
            })
        

class GetLedgerBalance(APIView):
    def get(self , request):
        payload = verify_token(request)
        try:
            user = User.objects.filter(id=payload['id']).first()
        except:
            return payload
        
        ledger_balance_instance = ledger_balance.objects.get(ledger_id=id)
        user_permission = check_user_company_right("Opening Balance", ledger_balance_instance.company_master_id, user.id, "can_view")
        if user_permission:
            serializer = GetLedgerBalanceSerializer(ledger_balance_instance)
            return Response({
            'success': True,
            'message':'',
            'data': serializer.data
            })
        else:
            return Response({
                'success': False,
                'message': 'You are not allowed to view Ledger Balance',
                'data': []
            })
        


class EDitLedgerBalance(APIView):
    def put(self, request, id):
        payload = verify_token(request)
        try:
            use = User.objects.filter(id=payload['id']).first()
        except:
            return payload
        
        user_permission = check_user_company_right("Opening Balance", request.data['company_master_id'], user.id, "can_alter")
        if user_permission:
            ledger_balance_instance = ledger_balance.objects.get(id=id)
            temp = request.data
            context = temp.dict()
            context['year_id'] = ledger_balance_instance.year_id.id
            debit = 0
            credit = 0

            if request.data['dr']:
                debit = D(request.data['dr'])
                context['fc_amount'] = D(request.data['fc_amount'])

            if request.data['cr'] :
                credit =(-1)*D(request.data['cr'])
                context['fc_amount'] = (-1)*D(request.data['fc_amount'])
            balance = debit+credit
            context['balance'] = balance
            if context['fc_amount'] == 0:
                fc_rate = "0"
            else:
                fc_rate = str(balance/D(context['fc_amount']))

            if fc_rate[0] == "-":
                fc_rate = fc_rate[1:]
            fc_rate = round(D(fc_rate), 4)
            #request.data.update({"fc_rate": fc_rate})
            context['fc_rate'] = fc_rate
            serializer = LedgerBalanceSerializer(ledger_balance_instance, data=context)

            if not serializer.is_valid():
                return Response({
                    'success': False,
                    'message': get_error(serializer.errors),
                    })

            serializer.save()
            return Response({
                'success': True,
                'message': 'ledger balance Edited successfully'})
        else:
            return Response({
                'success': False,
                'message': 'You are not allowed to Add ledger balance',
            })



class DeleteLedgerBalance(APIView):
    def delete(self, request):
        payload = verify_token(request)
        try:
            user = User.objects.filter(id=payload['id']).first()
        except:
            return payload
        ledger_balance_instance = ledger_balance.objects.get(id=id)
        user_permission = check_user_company_right("Opening Balance", ledger_balance_instance.company_master_id, user.id, "can_delete")
        if user_permission:
            ledger_balance_instance.altered_by = user.email
            ledger_balance_instance.delete()
            return Response({
                'success': True,
                'message': 'Ledger Balance deleted Successfully',
                })
        else:
            return Response({
                'success': False,
                'message': 'You are not allowed to delete Ledger balance',
            })
        


class AddLedgerBalBillwise(APIView):
    def post(self, request):
        payload = verify_token(request)
        try:
            user= User.objects.filer(id=payload['id']).first()
        except:
            return payload
        
        user_permission = check_user_company_right("Opening Balance", request.data['company_master_id'], user.id, "can_create")
        if user_permission:
            temp = request.data
            context = temp
            debit = 0
            credit = 0
            if request.data['dr']:
                temp = request.data
                context = temp
                debit = 0
                credit = 0
                if request.daat['dr']:
                    debit = D(request.data['dr'])
                if request.data['cr']:
                    credit = D(request.data['cr'])
                    balance = debit+credit
            #request.data.update({"amount":balance})
            context['amount'] = balance
            if D(context['fc_amount']) == 0:
                fc_rate = "0"
            else:
                fc_rate = str(balance/D(context['fc_amount']))
            
            if fc_rate[0] == "-":
                fc_rate = fc_rate[1:]
            fc_rate = round(D(fc_rate), 4)
            #request.data.update({"fc_rate": fc_rate})
            context['fc_rate'] = fc_rate
            serializer = LedgerBalanceBillwiseSerializer(data=context)
            if not serializer.is_valid():
                return Response({
                    'success': False,
                    'message': get_error(serializer.errors),
                    })

            serializer.save()
            return Response({
                'success': True,
                'message': 'ledger balance billwise added successfully'})
        else:
            return Response({
                'success': False,
                'message': 'You are not allowed to Add ledger balance billwise',
            })


def update_ledger_balance(id):
    balance = 0
    fc_amt = 0
    ledger_bal_instance = ledger_balance.objects.get(id=id)
    ledger_bal_billwise_instance = ledger_bal_billwise.objects.filter(ledger_bal_id = id)
    for i in ledger_bal_billwise_instance:
        balance += i.amount
        fc_amt += i.fc_amount
    ledger_bal_instance.balance = balance
    if(balance < 0):
        str_bal = str(balance)
        str_bal = str_bal[1:]
        ledger_bal_instance.cr = D(str_bal)
        ledger_bal_instance.dr = 0 
        ledger_bal_instance.total_cr = D(str_bal)
        ledger_bal_instance.total_dr = 0
    else:
        ledger_bal_instance.dr = balance
        ledger_bal_instance.cr = 0 
        ledger_bal_instance.total_dr = balance
        ledger_bal_instance.total_cr = 0
    if fc_amt == 0:
        fc_rate = "0"
    else:
        fc_rate = str(balance/fc_amt)   
        if fc_rate[0] == "-":
                fc_rate = fc_rate[1:]
        fc_rate = round(D(fc_rate), 4)
    ledger_bal_instance.fc_rate = fc_rate
    ledger_bal_instance.save()



class EditLedgerBalBillWise(APIView):
    def put(self, request, id):
        payload = verify_token(request)

        try:
            user = User.objects.filter(id=payload['id']).first()
        except:
            return payload
        
        user_permission = check_user_company_right("Opening Balance", request.data['company_master_id'], user.id, "can_alter")
        if user.perission:
            ledger_balance_billwise_instance = ledger_bal_billwise.objects.get(id=id)
            temp = request.data
            context = temp.dict()
            debit = 0 
            credit = 0
            if request.data['dr'] :
                debit = D(request.data['dr'])
            if request.data['cr'] :
                credit = D(request.data['cr'])
            balance = debit-credit
            #request.data.update({"balance":balance})
            context['amount'] = balance
            if D(context['fc_amount']) == 0:
                fc_rate = "0"
            else:
                fc_rate = str(balance/D(context['fc_amount']))
            # fc_rate = str(balance/D(request.data['fc_amount']))
            if fc_rate[0] == "-":
                fc_rate = fc_rate[1:]
            fc_rate = round(D(fc_rate), 4)
            #request.data.update({"fc_rate": fc_rate})
            context['fc_rate'] = fc_rate
            serializer = LedgerBalanceBillwiseSerializer(ledger_balance_billwise_instance, data=context)
            if not serializer.is_valid():
                return Response({
                    'success': False,
                    'message': get_error(serializer.errors),
                    })

            serializer.save()
            update_ledger_balance(ledger_balance_billwise_instance.ledger_bal_id.id)
            return Response({
                'success': True,
                'message': 'ledger balance billwise edited successfully'})
        else:
            return Response({
                'success': False,
                'message': 'You are not allowed to edit ledger balance billwise',
            })
        


class DeleteLedgerBalBillwise(APIView):
    def delete(self, request, id):
        # verify token
        payload = verify_token(request)
        try:
            user = User.objects.filter(id=payload['id']).first()
        except:
            return payload
        ledger_balance_billwise_instance = ledger_bal_billwise.objects.get(id=id)
        user_permission = check_user_company_right("Opening Balance", ledger_balance_billwise_instance.company_master_id, user.id, "can_delete")
        if user_permission:

            ledger_balance_billwise_instance.delete()
            update_ledger_balance(ledger_balance_billwise_instance.ledger_bal_id.id)
            return Response({
                'success': True,
                'message': 'Ledger Balance Billwie deleted Successfully',
                })
        else:
            return Response({
                'success': False,
                'message': 'You are not allowed to delete Ledger balance Billwise',
            })


# API For getting ledger balance billwise
# request : GET
# endpoint : get-ledger-bal-billwise/id (company id)
class GetLedgerBalBillwise(APIView):
    def get(self, request, id):
        payload = verify_token(request)
        try:
            user = User.objects.filter(id=payload['id']).first()
        except:
            return payload

        ledger_balance_billwise_instance = ledger_bal_billwise.objects.filter(ledger_bal_id=id)
        ledger_balance_instance = ledger_balance.objects.get(id=id)
        user_permission = check_user_company_right("Opening Balance", ledger_balance_instance.company_master_id, user.id, "can_view")
        if user_permission:
           
            serializer = LedgerBalanceBillwiseSerializer(ledger_balance_billwise_instance, many=True)
            return Response({
            'success': True,
            'message':'',
            'data': serializer.data
            })
        else:
            return Response({
                'success': False,
                'message': 'You are not allowed to view Ledger Balance',
                'data': []
            })
        



class AddOpBalBrs(APIView):
    def post(self, request):
        payload = verify_token(request)
        try:
            user = User.objects.filter(id=payload['id']).first()
        except:
            return payload

        user_permission = check_user_company_right("Opening Balance", request.data['company_master_id'], user.id, "can_create")
        if user_permission:
            year_master_instance = year_master.objects.get(company_master_id=request.data['company_master_id'], year_no=1)
            # request.data.update({"year_id":year_master_instance})
            temp = request.data
            context = temp.dict()
            context['year_id'] = year_master_instance.id

            serializer = OpBalanceBrsSerializer(data=context)
            if not serializer.is_valid():
                return Response({
                    'success': False,
                    'message': get_error(serializer.errors),
                    })

            serializer.save()
            return Response({
                'success': True,
                'message': 'Opening balance BRS added successfully'})
        else:
            return Response({
                'success': False,
                'message': 'You are not allowed to add Opening balance BRS',
            })
        


class EditOpBalBrs(APIView):
    def put(self, request, id):
        # verify token for authorization
        payload = verify_token(request)
        try:
            user = User.objects.filter(id=payload['id']).first()
        except:
            return payload

        
        user_permission = check_user_company_right("Opening Balance", request.data['company_master_id'], user.id, "can_alter")
        if user_permission:
            op_bal_brs_instance = op_bal_brs.objects.get(id=id)
            # request.data.update({"year_id":op_bal_brs_instance.year_id})
            temp = request.data
            context = temp.dict()
            context['year_id'] = op_bal_brs_instance.year_id.id
            serializer = OpBalanceBrsSerializer(op_bal_brs_instance, data=context)
            if not serializer.is_valid():
                return Response({
                    'success': False,
                    'message': get_error(serializer.errors),
                    })

            serializer.save()
            return Response({
                'success': True,
                'message': 'Opening balance BRS edited successfully'})
        else:
            return Response({
                'success': False,
                'message': 'You are not allowed to edit Opening balance BRS',
            })
        


class DeleteOpBalBrs(APIView):
    def delete(self, request, id):
        # verify token
        payload = verify_token(request)
        try:
            user = User.objects.filter(id=payload['id']).first()
        except:
            return payload

        op_bal_brs_instance = op_bal_brs.objects.get(id=id)
        user_permission = check_user_company_right("Opening Balance", op_bal_brs_instance.company_master_id, user.id, "can_delete")
        if user_permission:
            op_bal_brs_instance.altered_by = user.email
            op_bal_brs_instance.delete()
            return Response({
                'success': True,
                'message': 'Opening balance BRS deleted Successfully',
                })
        else:
            return Response({
                'success': False,
                'message': 'You are not allowed to delete Opening balance BRS',
            })


class GetOpBaslBrs(APIView):
    def get(self, request, id):
        payload = verify_token(request)
        try:
            user = User.objects.filter(id=payload['id']).first()
        except:
            return payload
        
        user_permission = check_user_company_right("Opening Balance", id, user.id, "can_view")
        if user_permission:
            op_bal_brs_instance = op_bal_brs.objects.filter(company_master_id=id)
            serializer = GetOpBalanceBrsSerializer(op_bal_brs_instance, many=True)
            return Response({
                'success':True, 
                'message':'',
                'data':serializer.data
            })
        else:
            return Reponse({
                'success':False,
                'message':'you are not allowed to view opening balance BRS',
                'data':[]
            })


class GetDetailOpBalBrs(APIView):
    def get(self, request, id):
        payload = verify_token(request)
        try:
            user = User.objects.filter(id=payload['id']).first()
        except:
            return payload
        
        op_bal_brs_instance = op_bal_brs.objects.get(id=id)
        user_permission = check_user_company_right("Opening Balance", op_bal_brs_instance.company_master_id, user.id, "can_view")
        if user_permission:

            serializer = GetOpBalanceBrsSerializer(op_bal_brs_instance)
            return Response({
                'success':False,
                'message':'You are allowed to view opening balance BRS',
                'data': []
            })
