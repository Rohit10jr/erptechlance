from rest_framework import serializers
from rest_framework.views import APIView
from .models import User, transaction_right, user_group, user_right


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'name', 'email', 'password','is_superuser','created_by']
        extra_kwargs = {
            'password': {'write_only': True},
            'id':{'read_only': True},
            'created_on':{'read_only': True},
            'altered_by': {'write_only': True}
        }


    def update(self, instance, validated_data):
        if(instance.password):
            for attr, value in validated_data.items():
                if attr == 'password' and value!=None:
                    instance.set_password(value)
                elif attr == 'password' and value==None:
                    pass
                else:
                    setattr(instance, attr, value)
            instance.save()
            return instance
        else:
            instance.save()
            return instance


    def create(self, validated_data):
        password = validated_data.pop('password', None)
        instance = self.Meta.model(**validated_data)
        if password is not None:
            instance.set_password(password)
        instance.save()
        return instance

class UsernamesSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'name', 'email']


class UserGroupSerializer(serializers.ModelSerializer):
    class Meta:
        model = user_group
        fields = '__all__'
        extra_kwargs = {
            'id':{'read_only':True},
            'created_on':{'read_only':True},
            'altered_by':{'write_only':True}
        }

        def create(self, validated_data):
            instance = self.Meta.model(**validated_data)
            instance.save()
            return instance
        
        def update(self, instance, validated_data):
            for attr, value in validated_data.items():
                setattr(instance, attr, value)
            instance.save()
            return instance


class UserRightSerializer(serializers.ModelSerializer):
    class Meta:
        model = user_right
        fields = '__all__'
        extra_kwargs = {
            'id':{'read_only':True},
            'created_on':{'read_only':True },
            'altered_on':{'write_only':True }
        }

    def create(self, validated_data):
        instance = self.Meta.model(**validated_data)
        instance.save()
        return instance
    
    def update(self, instance, validated_data):
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        return instance


class TransactionRightSerializer(serializers.ModelSerializer):
    class Meta:
        model = transaction_right
        fields = '__all__'
        extra_kwargs = {
            'id':{'read_only':True},
            'creatd_on':{'read_only':True},
            'altered_by':{'write_only':True}
        }


class GetUserRightSerializer(serializers.ModelSerializer):
    trancstion_id = TransactionRightSerializer()
    class Meta:
        model = user_right
        # fields = '__all__' 
        exclude = ('user_group_id')
        extra_kwargs = {
            "id":{'read_only':True},
            "created_on":{'read_only':True},
            "altered_by":{'write_only':True}
        }