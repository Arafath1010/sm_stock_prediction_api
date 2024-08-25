from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import data_collector as dc
import pandas as pd
from prophet import Prophet
import math
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def insert_data(b_id,forecast_data):#mysql-connector-python
    import mysql.connector
    import json
    
    # Define connection parameters
    host = "68.183.225.237"
    user = "sm_ml"
    password = "Fz6/I733"
    database = "sm_qa_1"
    
    # Establish connection
    connection = mysql.connector.connect(
        host=host,
        user=user,
        password=password,
        database=database
    )
    # Create a cursor object
    cursor = connection.cursor()
    # Convert forecast_data to JSON string
    forecast_data_json = json.dumps(forecast_data)
    
    # SQL command to insert data
    insert_query = """
    INSERT INTO sm_product_count_forecast (bid, forecast_data)
    VALUES (%s, %s)
    """
    
    # Execute the SQL command with data
    cursor.execute(insert_query, (b_id, forecast_data_json))
    
    # Commit the transaction
    connection.commit()
    
    print("Data inserted successfully")
    
    # Close the cursor and connection
    cursor.close()
    connection.close()


def delete_json(b_id):
    import mysql.connector
    
    # Define connection parameters
    host = "68.183.225.237"
    user = "sm_ml"
    password = "Fz6/I733"
    database = "sm_qa_1"
    
    # Establish connection
    connection = mysql.connector.connect(
        host=host,
        user=user,
        password=password,
        database=database
    )
    # Create a cursor object
    cursor = connection.cursor()
    # SQL command to delete a specific record
    delete_query = """
    DELETE FROM sm_product_count_forecast
    WHERE bid = %s
    """
    
    # Execute the SQL command with the specified BID
    cursor.execute(delete_query, (b_id,))
    # Commit the transaction
    connection.commit()
    print(f"Record with BID {b_id} deleted successfully")
    # Close the cursor and connection
    cursor.close()
    connection.close()

def get_data(b_id):
    import mysql.connector
    import json
    
    # Define connection parameters
    host = "68.183.225.237"
    user = "sm_ml"
    password = "Fz6/I733"
    database = "sm_qa_1"
    
    # Establish connection
    connection = mysql.connector.connect(
        host=host,
        user=user,
        password=password,
        database=database
    )
    
    # Create a cursor object
    cursor = connection.cursor()
    
    # SQL command to select data for a specific BID
    select_query = """
    SELECT bid, forecast_data, created_at
    FROM sm_product_count_forecast
    WHERE bid = %s
    """
    
    # Execute the SQL command with the specified BID
    cursor.execute(select_query, (b_id,))
    
    # Fetch the result
    row = cursor.fetchone()
    
    if row:
        bid = row[0]
        forecast_data_json = row[1]
        created_at = row[2]
        
        # Convert JSON string back to Python dictionary
        forecast_data = json.loads(forecast_data_json)
        result = {
            "BID":bid,
            "created_at":created_at,
            "forecast_data":forecast_data
        }
        return result
        
    else:
        return None
    
    # Close the cursor and connection
    cursor.close()
    connection.close()


def forecast(monthly_sales):
    # Prepare the data for Prophet
    monthly_sales.rename(columns={'transaction_date': 'ds', 'sell_qty': 'y'}, inplace=True)

    # Initialize and fit the Prophet model
    model = Prophet()
    model.fit(monthly_sales)

    # Make a future dataframe for the next month
    future = model.make_future_dataframe(periods=1, freq='M')
    forecast = model.predict(future)

    # Extract the forecasted sales for the next month
    forecasted_sales = forecast[['ds', 'yhat']].tail(2)

    # Combine historical and forecasted data
    combined_sales = pd.concat([monthly_sales, forecasted_sales[-1:]], ignore_index=True)
    original_forecasted_value = combined_sales.tail(1)
    rounded_value = combined_sales.tail(1)

    rounded_value['yhat'] = rounded_value['yhat'].apply(lambda x: max(0, math.ceil(x)))

    return combined_sales, original_forecasted_value, rounded_value

def process_product(product_name, data):
    full_trend = ""
    try:
        # Get today's date
        today = datetime.today().strftime('%Y-%m-%d %H:%M:%S')
    
        # Create a new fake transaction with today's date and selling count 0
        fake_transaction = data.iloc[0].copy()
        fake_transaction['transaction_date'] = today
        fake_transaction['sell_qty'] = 0
    
        # Convert fake_transaction to a DataFrame
        fake_transaction_df = pd.DataFrame([fake_transaction])
    
        # Concatenate the original DataFrame with the new fake transaction DataFrame
        data = pd.concat([data, fake_transaction_df], ignore_index=True)
        
        # Summarize the sales count per month
        data['transaction_date'] = pd.to_datetime(data['transaction_date'])
        data.set_index('transaction_date', inplace=True)
        monthly_sales = data['sell_qty'].resample('M').sum().reset_index()

        full_trend, forecasted_value, rounded_value = forecast(monthly_sales)
        rounded_value.columns = ["next_month", "y", "predicted_count"]
        # Convert to dictionary
        result_dict = rounded_value.to_dict(orient="records")[0]

        return {
            "Product Name": product_name,
            "next_month": str(result_dict["next_month"]),
            "predicted_count": result_dict["predicted_count"]
            #"full_trend" : str(full_trend)
        }
    except Exception as e:
        return {
            "Product Name": product_name,
            "next_month": str(e),
            "predicted_count": "not predicted"
            #"full_trend" : str(full_trend)
        }

@app.post("/generate_product_count_prediction")
async def generate_product_count_prediction(b_id: int):
    try:
        # main
        data, message = dc.get_data(b_id=b_id, product_name="sample")

        if message == "done":

            grouped_df = data.groupby('product_name')

            results = []
            with ThreadPoolExecutor() as executor:
                futures = [executor.submit(process_product, product_name, product_df.copy()) for product_name, product_df in grouped_df]
                for future in as_completed(futures):
                    results.append(future.result())


            delete_json(b_id)
            insert_data(b_id,results)
            return {"status": "success",
                    "b_id":b_id,
                    "message": "Prediction successful and saved to DB",
                    "status_code":200
                   }
            

    except Exception as e:
        print(str(e))
        response_content = {
            "status": "error",
            "message": str(e),
            "data": None,
            "status_code":200
        }
        return response_content


@app.post("/get_product_count_prediction_from_DB")
async def get_product_count_prediction_from_DB(b_id: int):
        response_content = {
            "status": "done",
            "message": "data from DB",
            "data": get_data(b_id),
            "status_code":200
        }
        return response_content
