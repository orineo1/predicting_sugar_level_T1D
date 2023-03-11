import numpy as np
import pandas as pd
from pymongo import MongoClient
from numpy.linalg import inv
import random

# The functions of the algorithm for predicting sugar levels

def connect_mongo(db_name,collection_name,uri):
    """
    According to the DB name, the collection_name and the uri contact the BG DB
    """
    # set up MongoDB connection
    mongo_uri=uri
    client = MongoClient(mongo_uri) 

    db = client[db_name]
    collection = db[collection_name]

    return collection


def read_obs_mongo(numb_obs,collection):

    """
    Extracts numb_obs (int) rows from the collection of sugar levels (DB)
    """
    # sort documents by _id in descending order and limit to last 100 documents
    cursor = collection.find().sort('_id', -1).limit(numb_obs)

    # read data into Pandas DataFrame
    data = pd.DataFrame(list(cursor))

    return data

def currnet_bg_val(collection,numb_read):
    """"
    A function that returns the number of the last readings (numb_read-int)  of sugar from the collection(DB)
    """
    curr_values = np.flip(np.array(read_obs_mongo(numb_read,collection)["sgv"]))
    if numb_read==1:
        return int(curr_values[0])
    return curr_values

def calbration_start(entries_df,Z,Epsilon,T,alpha,P,Eta):
    """"
    Adjustment and updating of the various matrices according to the Kalman Filter
    """
    last_relevant_obs =np.flip(np.array(entries_df["sgv"]))

    for i in range(len(last_relevant_obs)):
        # Predict the next state
        alpha = T @ alpha
        P = T @ P @ T.T + Eta

        # Update the state using the new measurement
        K = P @ Z.T @ inv(Z @ P @ Z.T + Epsilon)
        alpha = alpha + K @ (last_relevant_obs[i] - Z @ alpha)
        P = (np.eye(2) - K @ Z) @ P
    return alpha,P


def predict(Z,T,alpha,numb_pred):
    """
    Prediction of the next n (int) readings of sugar levels using a Kalman filter
    """
    next_predictions = [int(Z@  np.linalg.matrix_power(T  , i)@ alpha ) for i in range(1,numb_pred+1)] 
    return next_predictions

def init_vectors_and_matrix():
    """
    A function that initializes the initial variables for the Kalman filter
    """

    # Define the initial state
    alpha = np.array([[0], [0]])

    # Define the initial covariance matrix
    P = np.array([[1, 0], [0, 1]])

    # Define the state transition matrix
    T = np.array([[1, 1], [0, 1]])

    # Define the measurement matrix
    Z = np.array([[1, 0]])

    # Define the measurement noise covariance matrix
    Epsilon = np.array([[1]])

    # Define the process noise covariance matrix
    Eta = np.array([[0.1, 0], [0, 0.1]])
    
    return alpha,P,T,Z,Epsilon,Eta

# The number of previous observations includes the current observation with which the transition matrix is updated
number_of_obs_to_update = 9

def main_cgm(collection_mongo,mse_calc=False,mse_df=[]): # , Z=Z,Epsilon=Epsilon,T=T,alpha=alpha,P=P,Eta=Eta
    """
    The central function, to implement the kalman prediction algorithm
    Retrieves the last number_of_obs_to_update readings, updates the values of the matrices and predicts as the requested number of times
    """
    alpha,P,T,Z,Epsilon,Eta = init_vectors_and_matrix()
    entries_df = mse_df

    if not mse_calc:
        entries_df = read_obs_mongo(number_of_obs_to_update,collection_mongo)
    
    
    alpha,P  = calbration_start(entries_df,Z,Epsilon,T,alpha,P,Eta)

    next_pred = predict(Z,T,alpha,numb_pred=5) 
    return next_pred



 ######################## MSE CALCULATIONS ########################

def calcualte_mse(BG_level_df,iterations,numb_pred=2,which_reading=1):
    """"
    A function to calculate the mse of the algorithm

    BG_level_df: df from mongodb that contains the sugar data and dates
    iterations: Calculating the mse on how many predicted observations
    numb_pred: How many steps forward in sugar values will be considered in the mse calculation
    which_reading : on which forecast to calculate the MSE (between 1 and numb_pred)
    """
    global number_of_obs_to_update
    # variable that contains the sum of the subtraction between the prediction and the actual result squared
    squared_sum_pred_vs_real = 0
    for i in range(iterations):
        # random starting point selection - limited to an index of number_of_obs_to_update prior to the last observation (the predictions is calculated on number_of_obs_to_update observations)
        starting_point=random.randint(1, len(BG_level_df)-(number_of_obs_to_update+1+numb_pred))
        # Choice of the next number_of_obs_to_update readings
        temp_bg_df = BG_level_df.iloc[starting_point:starting_point+number_of_obs_to_update,:].sort_values(by="date",
                                                                                        ascending=False) 
        # calculate the predictions and save the real םbservations
        predictions = np.array(main_cgm(None, Z=Z,Epsilon=Epsilon,T=T,alpha=alpha,P=P,Eta=Eta,
        mse_calc=True,mse_df=temp_bg_df) [which_reading-1])
        real_obs = np.array(BG_level_df.iloc[starting_point+number_of_obs_to_update:starting_point+number_of_obs_to_update+numb_pred,:]["sgv"])[which_reading-1]
            
        # subtraction the distance between the forecast and the actual value squared  
        squared_sum_pred_vs_real+= ((predictions-real_obs)**2).sum()
        
    # average over all predictions
    mse =  squared_sum_pred_vs_real/(iterations)  
    return  "The MSE of  the {} reading ahead over {} iterations is {}".format(which_reading,iterations,mse)


# # # variables to calcualte mse function
# path_to_bg_level_df = "name_of_csv"
# BG_level_df = pd.read_csv(path_to_bg_level_df+".csv")
# # calcualte_mse(BG_level_df,40000,numb_pred=5,which_reading=1)


