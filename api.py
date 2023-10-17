from botocore.exceptions import ClientError
import json
# flask
from flask import Blueprint, request, jsonify
from flask_swagger_ui import get_swaggerui_blueprint

api_blueprint = Blueprint('api_v1', __name__)

# swagger configs
SWAGGER_URL = '/docs'  # URL for exposing Swagger UI (without trailing '/')
API_URL = '/static/swagger.json'  # Our API url (can of course be a local resource)

# # Call factory function to create our blueprint
swaggerui_blueprint = get_swaggerui_blueprint(
    SWAGGER_URL,  # Swagger UI static files will be mapped to '{SWAGGER_URL}/dist/'
    API_URL,
    config={  # Swagger UI config overrides
        'app_name': "Test application"
    },
)

api_blueprint.register_blueprint(swaggerui_blueprint)

# Health check
@api_blueprint.route('/health', methods=['GET'])
def health():
    response = {'message': 'Retimark Diabetes Management API Server is running'}
    return jsonify(response), 200

# Create a user
@api_blueprint.route('/user', methods=['POST'])
def create_user():
    from app import cip, db
    try:
        # Get the access token from the header
        access_token = request.headers.get('access_token') or "Dummy-String"
        # Verify the access token 
        # _ = cip.get_user(access_token)
        # Get the user data from the request body
        user_data = request.get_json()
        # Store the user data
        insert_query = """
        INSERT INTO Users (
            UserName, FullName, Email, Birthdate, Gender, risk_score_goal
        ) VALUES (
            %s, %s, %s, %s, %s, %s
        )
        """        
        try:
            with db.cursor() as cursor:
                cursor.execute(insert_query, (
                    user_data['username'], user_data['fullname'], f'\'{user_data["email"]}\'',
                    user_data['birthdate'], user_data['gender'],user_data['risk_score_goal']
                ))
                # Commit the change to database
                db.commit()
        except Exception as e:
            response = {'error': f"Failed to add user to database: {e}"}
            db.rollback()
            return jsonify(response), 500
        
        response = {'message': 'User created successfully'}
        return jsonify(response), 200
    except ClientError:
        response = {'error': 'Unauthorised'}
        return jsonify(response), 401
    except Exception as e:
        response = {'error': str(e)}
        return jsonify(response), 500

# Get all users
@api_blueprint.route('/users', methods=['GET'])
def get_users():
    from app import db
    try:
        cursor = db.cursor()
        cursor.execute(
            "SELECT * FROM Users"
        )
        users = cursor.fetchall()
        return jsonify(list(users)), 200

    except Exception as e:
        response = {'error': str(e)}
        return jsonify(response), 500
    finally:
        cursor.close()

# Get user by given email
@api_blueprint.route('/user/<string:email>', methods=['GET'])
def get_user(email):
    from app import cip, db
    try:
        # Get the access token from the header
        access_token = request.headers.get('access_token') or "Dummy-String"
        #Verify the access token 
        # _ = cip.get_user(access_token)
        
        with db.cursor() as cursor:
            cursor.execute(
                "SELECT * FROM Users "
                "WHERE Users.Email = '''{}'''".format(email)
            )
            user = cursor.fetchone()
            if user is None:
                response = {"error": "User not found"}
                return jsonify(response), 404
            return jsonify(user), 200
    except ClientError:
        response = {'error': 'Unauthorised'}
        return jsonify(response), 401 
    except Exception as e:
        response = {'error': str(e)}
        return jsonify(response), 500 

# Update user by given email
@api_blueprint.route('/user/<string:email>', methods=['PUT'])
def update_user(email):
    from app import cip, db
    try:
        # Get the access token from the header
        access_token = request.headers.get('access_token')
        #Verify the access token 
        # _ = cip.get_user(access_token)
        # Get the user data from the request body
        update_data = request.get_json()

        with db.cursor() as cursor:
            cursor.execute(
                "SELECT * FROM Users "
                "WHERE Users.Email = '''{}'''".format(email)
            )
            user = cursor.fetchone()
            if user is None:
                response = {"error": "User not found"}
                return jsonify(response), 404
            
            updates = update_data['updates']
            for update in updates:
                column = update['column']
                value = update['value']
                sql = f"UPDATE Users SET {column} = %s WHERE Users.Email = %s"
                cursor.execute(sql, (value, f'\'{email}\''))
            db.commit()
        response = {'message': 'Sucessfully update user'}
        return jsonify(response), 200

    except ClientError as ce:
        response = {'error': 'Unauthorised'}
        return jsonify(response), 401        
    except Exception as e:
        response = {'error': str(e)}
        db.rollback()
        return jsonify(response), 500 
# Delete user with given email
@api_blueprint.route('/user/<string:email>', methods=['DELETE'])
def delete_user(email):
    from app import cip, db
    try:
        # Get the access token from the header
        access_token = request.headers.get('access_token')
        #Verify the access token 
        # _ = cip.get_user(access_token)

        with db.cursor() as cursor:
            cursor.execute(
                "SELECT * FROM Users "
                "WHERE Users.Email = '''{}'''".format(email)
            )
            user = cursor.fetchone()
            if user is None:
                response = {"error": "User not found"}
                return jsonify(response), 404
            delete_reports(email)
            cursor.execute("DELETE FROM Users "
                           "WHERE Users.Email = '''{}'''".format(email))
            db.commit()
        response = {'message': 'Sucessfully delete user'}
        return jsonify(response), 200

    except ClientError as ce:
        response = {'error': 'Unauthorised'}
        return jsonify(response), 401        
    except Exception as e:
        response = {'error': str(e)}
        db.rollback()
        return jsonify(response), 500 
# Create Report
@api_blueprint.route('/report', methods=['POST'])
def create_report():
    from app import cip, db
    try:
        # Get the access token from the header
        access_token = request.headers.get('access_token')
        #Verify the access token 
        # _ = cip.get_user(access_token)

        report_data = request.get_json()
        # Store the user data
        insert_query = f"""
        INSERT INTO past_report (
            email, age, HE_sbp, HE_dbp, HE_ht, HE_wt, HE_wc, HE_BMI, HE_glu, HE_HbA1c, HE_chol, HE_HDL_st2, HE_TG,
            DE1_dur, eGFR, sex, DE1_31, DE1_32, HE_HP_2c, HE_HCHOL, HE_DMfh, sm_presnt_3c, HE_obe_6c, diagnosis_time,
            diagnosed_class, risk_score, risk_score_glucose_50, predicted_class_glucose_50, risk_score_glucose_75,
            predicted_class_glucose_75, risk_score_glucose_100, predicted_class_glucose_100
        ) VALUES (
            %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
            %s, %s, %s, %s, %s, %s, %s
        )
        """
        try:
            with db.cursor() as cursor:
                cursor.execute(
                    "SELECT * FROM Users "
                    "WHERE Users.Email = '''{}'''".format(report_data["email"])
                )
                user = cursor.fetchone()
                if user is None:
                    response = {"error": "User not found"}
                    return jsonify(response), 404
                
                cursor.execute(insert_query, (
                    f'\'{report_data["email"]}\'',
                    report_data['age'],
                    report_data['HE_sbp'],
                    report_data['HE_dbp'],
                    report_data['HE_ht'],
                    report_data['HE_wt'],
                    report_data['HE_wc'],
                    report_data['HE_BMI'],
                    report_data['HE_glu'],
                    report_data['HE_HbA1c'],
                    report_data['HE_chol'],
                    report_data['HE_HDL_st2'],
                    report_data['HE_TG'],
                    report_data['DE1_dur'],
                    report_data['eGFR'],
                    report_data['sex'],
                    report_data['DE1_31'],
                    report_data['DE1_32'],
                    report_data['HE_HP_2c'],
                    report_data['HE_HCHOL'],
                    report_data['HE_DMfh'],
                    report_data['sm_presnt_3c'],
                    report_data['HE_obe_6c'],
                    report_data['diagnosis_time'],
                    report_data['diagnosed_class'],
                    report_data['risk_score'],
                    report_data['risk_score_glucose_50'],
                    report_data['predicted_class_glucose_50'],
                    report_data['risk_score_glucose_75'],
                    report_data['predicted_class_glucose_75'],
                    report_data['risk_score_glucose_100'],
                    report_data['predicted_class_glucose_100']
                ))
                # Commit the change to database
                db.commit()
        except Exception as e:
            response = {'error': f"Failed to add report to database: {e}"}
            db.rollback()
            return jsonify(response), 500
        
        response = {'message': 'Report created successfully'}
        return jsonify(response), 200

    except ClientError:
        response = {'error': 'Unauthorised'}
        return jsonify(response), 401        
    except Exception as e:
        response = {'error': str(e)}
        db.rollback()
        return jsonify(response), 500 
# Get all reports of given email
@api_blueprint.route('/reports/<string:email>', methods=['GET'])
def get_reports(email):
    from app import cip, db
    try:
        # Get the access token from the header
        access_token = request.headers.get('access_token') or "Dummy-String"
        #Verify the access token 
        # _ = cip.get_user(access_token)
        
        with db.cursor() as cursor:
            cursor.execute(
                "SELECT * FROM Users "
                "WHERE Users.Email = '''{}'''".format(email)
            )
            user = cursor.fetchone()
            if user is None:
                response = {"error": "User not found"}
                return jsonify(response), 404
            cursor.execute(
                "SELECT * FROM past_report "
                "WHERE email = '''{}'''".format(email)
            )
            reports = cursor.fetchall()            
            return jsonify(list(reports)), 200
    except ClientError:
        response = {'error': 'Unauthorised'}
        return jsonify(response), 401 
    except Exception as e:
        response = {'error': str(e)}
        return jsonify(response), 500 
    
def delete_reports(email):
    from app import cip, db
    try:
        # Get the access token from the header
        # access_token = request.headers.get('access_token')
        #Verify the access token 
        # _ = cip.get_user(access_token)

        with db.cursor() as cursor:  
            cursor.execute("DELETE FROM past_report "
                           "WHERE email = '''{}'''".format(email))
            db.commit()

        return True       
    except Exception as e:
        db.rollback()
        return False
    
# Get most recent report of given email
@api_blueprint.route('/report/<string:email>', methods=['GET'])
def get_report(email):
    from app import cip, db
    try:
        # Get the access token from the header
        access_token = request.headers.get('access_token') or "Dummy-String"
        #Verify the access token 
        # _ = cip.get_user(access_token)
        
        with db.cursor() as cursor:
            cursor.execute(
                "SELECT * FROM Users "
                "WHERE Users.Email = '''{}'''".format(email)
            )
            user = cursor.fetchone()
            if user is None:
                response = {"error": "User not found"}
                return jsonify(response), 404
            sql = """
            SELECT *
            FROM past_report
            WHERE email = %s
            ORDER BY diagnosis_time DESC
            LIMIT 1
            """
            cursor.execute(sql, f'\'{email}\'')
            report = cursor.fetchone()            
            return jsonify(report), 200
    except ClientError:
        response = {'error': 'Unauthorised'}
        return jsonify(response), 401 
    except Exception as e:
        response = {'error': str(e)}
        return jsonify(response), 500 
# Other routes for getting, updating, and deleting users and reports can be similarly defined.