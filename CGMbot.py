from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
import os
import pandas as pd 
import asyncio
import numpy as np
import predictBGKalmnFilter as predKalman # Import functions from the predictBGKalmnFilter

######################## DEFINING THE CONSTANTS VARIABLES  ########################

# Create an empty dictionary for all the information required to run the algorithm
# 1. DB from which the information is drawn
# 2. For users who are allowed to run the application
# 3. TOKEN of the Telegram bot
# 4. Desired sugar values and the number of predictions in an undesirable range required in order to trigger an alert
init_data_dict = {}

# Open the text file for reading
with open('info_for_the_pred_algorithem - ORI.txt', 'r') as file:
    # Loop over each line in the file
    for line in file.readlines():

        key, value = line.strip().replace(" ", "").split('-')
        # Add the key-value pair to the dictionary
        init_data_dict[key] = float(value) if value.isdigit() else value


TOKEN = init_data_dict["TOKEN"]
# Enter the Telegram id of the users approved to use the bot
ALLOWED_IDS = [int(ID) for ID in init_data_dict["ALLOWED_IDS"].replace(" ", "").split(',')]

# Connecting to mongodb
collection_mongo = predKalman.connect_mongo(init_data_dict["DB_NAME"],init_data_dict["COLLECTION_NAME"],init_data_dict["URI_MONGO"])

# Initialization of the forecast(pred-predictions) table and the forecast index
total_pred = pd.DataFrame(index=range(5),columns=["next {}".format(i+1) for i in range(5)]) 
i=0

#An upper and lower limit from which the algorithm will start alerting
UPPER_BOUND = init_data_dict["UPPER_BOUND"] 
LOWER_BOUND = init_data_dict["LOWER_BOUND"] 

# The number of times of different predictions that are required for the bot to alert
Threshold_Alerts = init_data_dict["Threshold_Alerts"] 


######################## AUXILIARY FUNCTION FOR THE MAIN FUNCTIONS (AS THE MAIN ONES ARE BELOW) ########################

def numb_outer_bound(total_pred,treshold=Threshold_Alerts,lower_bound=LOWER_BOUND,upper_bound=UPPER_BOUND)->bool:
    """
    Helper function for the 'predict' function, its purpose is to find out if there are more than Threshold_Alerts(int) predictions in the total_pred(df) where the prediction goes out of bounds
    lower_bound(int) or upper_bound(int) 
    """
    return (total_pred.apply(lambda row: any(row<lower_bound ),axis=1).sum()>treshold) or (total_pred.apply(lambda row: any(row>upper_bound ),axis=1).sum()>treshold)  


async def predict( context: ContextTypes.DEFAULT_TYPE,collection_mongo=collection_mongo) -> None:
    """"
    A helper function for the start_pred_algorithm user function whose purpose is whether there was a change in the prediction from last time.
        If so, we will insert another row in the prediction table (total_pred) if not, the function will do nothing.
        If there are too many predictions of the desired range (calculated using numb_outer_bound), an output is returned to the user.
    """
    global total_pred,i,ALLOWED_IDS
    job = context.job

    # Prediction of the next 5 BG using Kalman filter
    predictions =   predKalman.main_cgm(collection_mongo)

    # In case there is no change from the previous predictions (there is no new sample yet, end the run
    if all(total_pred.iloc[(i-1)%5]==predictions):
        return
    
    # Update row i with the new predictions - '%' is used because there is no need for more than 5 predictions for the future and to save space
    total_pred.loc[i%5] = predictions
    i+=1
    print(total_pred)
    
    # If all predictions are within the desired range, stop
    if all(LOWER_BOUND<np.array(predictions)) and all (np.array(predictions)<UPPER_BOUND) :
        return    
    
    # If there is more than a Threshold_Alerts of different forecasts in which a lower or higher BG is expected than the UPPER_BOUND or LOWER_BOUND send a message to the user
    if numb_outer_bound(total_pred):
        predictions = ["Low" if predictions[i]<40 else predictions[i]  for i in range(3)]  # Conversion of values smaller than 40 to be "Low" - known convention
        await context.bot.send_message(job.chat_id, text=f"Unwanted predicted sugar values -\n The next predictions are {', '.join(list(map(str, predictions[:3])))}")


def remove_job_if_exists(name: str, context: ContextTypes.DEFAULT_TYPE) -> bool:
    """Remove job with given name. Returns whether job was removed."""
    current_jobs = context.job_queue.get_jobs_by_name(name)

    # Stop all tasks by chat ID
    if not current_jobs:
        return False
    for job in current_jobs:
        job.schedule_removal()
    return True


async def complx_snooze_finish(context: ContextTypes.DEFAULT_TYPE) -> None:
    """"
    A helper function for complx_snooze, and is part of the flow complx_snooze -> complx_snooze_is_in_condition->complx_snooze_finish.
    This function is the last in the sequence and its purpose is to restart the prediction algorithm and return to the user why the algorithm has started working again
    """
    job = context.job
    high_val ,chat_id = job.data

    context.job_queue.run_repeating(predict,  interval=60*2+30, first=1, chat_id=chat_id, name=str(chat_id))

    # If the current sugar value is higher than the value defined in complx_snooze, return a message
    if predKalman.currnet_bg_val(collection_mongo,1)>high_val:
        text = "BG level is going over then {}, prediction algorithem set again".format(high_val)
        await  context.bot.send_message(chat_id, text=text)
        return

    # In the case that the sugar value is not higher than the upper limit set and is probably lower than 140, return the appropriate message
    text = "BG level is going under then 140, the  algorithem set again"
    await  context.bot.send_message(chat_id, text=text)

async def complx_snooze_is_in_condition(context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    A helper function for complx_snooze, and is part of the flow complx_snooze -> complx_snooze_is_in_condition->complx_snooze_finish.

    The purpose of the function is to see if the condition of the complex snooze is still met -
    that is, whether the sugar values are above 140 and below the target value defined when running the complx_snooze (the value from which we want to run the prediction algorithm again).
    """
    job = context.job
    high_val ,chat_id = job.data

    curr_val = predKalman.currnet_bg_val(collection_mongo,1)

    # If the sugar level is in the desired range (between 140 and the upper limit set in complx_snooze, continue in the loop - The complex snooze conditions still apply
    while curr_val<high_val and curr_val>140 :
        await asyncio.sleep(2*60+30)
        # print("waited 2.5 min")
        curr_val = predKalman.currnet_bg_val(collection_mongo,1)
    
    # If the threshold is crossed in either direction, continue in flow to end the complex snooze to the function complx_snooze_finish
    context.job_queue.run_once(complx_snooze_finish, 1, chat_id=chat_id, name=str(chat_id), data=[high_val,chat_id] )

######################## THE MAIN COMMANDS OF THE BOT ########################

async def help(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Shows the user the active functions and an explanation of them
    """
    await update.message.reply_text("""Hello there and welcom to sugi_bot 😀👋\n
The purpose of the bot is to predict sugar levels and update the user with a message if the BG levels are going to go out of the desired range <a href='https://github.com/orineo1/predicting_sugar_level_T1D'>(Github page)</a>\n
<b>Bot Commands</b>
/start or /help -> show this message.
/start_predict -> starts running the prediction algorithem.
/stop_predict -> stops the prediction algorithem.
/simple_snooze -> stops the algorithem for 30 minutes and then excutes it again.
/complx_snooze 'number' -> stops the notifications until reaching the 'number' or getting bellow 140.
/next_bg -> prediction for the next 3 readings.
/last_5_bg -> sugar values for the previous 5 readings.
""", parse_mode='HTML',disable_web_page_preview=True)


async def start_pred_algorithm(update: Update, context = ContextTypes.DEFAULT_TYPE) -> None:
    """Initialization of the prediction algorithm"""
    global total_pred, ALLOWED_IDS

    # If the user is not authorized, stop
    chat_id = update.effective_message.chat_id
    if chat_id not in ALLOWED_IDS:
        await update.effective_message.reply_text("You do not have permissions to perform this action")
        return
    
    # Resetting the forecast table
    total_pred = pd.DataFrame(index=range(5),columns=["next {}".format(i+1) for i in range(5)])
    
    # If there is an active task - delete it
    job_removed = remove_job_if_exists(str(chat_id), context)

    # Iteratively run the algorithm
    context.job_queue.run_repeating(predict,  interval=60*2+30, first=2, chat_id=chat_id, name=str(chat_id))
    
    # Updating the user on the start of the algorithm
    text = "Start predection algorithem"
    if job_removed:
        text += ". Old one was removed."
    await update.effective_message.reply_text(text)


async def terminate_pred_algorithm (update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Remove the predictions job by user request"""
    chat_id = update.message.chat_id

    # If there is an active task - delete it
    job_removed = remove_job_if_exists(str(chat_id), context)

    # Updating the user
    text = "Predection successfully cancelled!" if job_removed else "You have no active predection algorithem running."
    await update.message.reply_text(text)


async def complx_snooze(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """"
    snooze for the user who does not disturb him until reaching an upper limit that the user types or until reaching below 140.
    Function as part of the flow complx_snooze -> complx_snooze_is_in_condition->complx_snooze_finish.
    """
    global total_pred
    chat_id = update.message.chat_id
    job_removed = remove_job_if_exists(str(chat_id), context)    # If there is an active job (prediction algorithm) - delete it

    # Checking whether the user has given an upper limit - if not return an error message
    try:high_border = int(context.args[0])
    except:
        await update.message.reply_text("didn't recive any values for the higher border, next time call /complx_snooze <number>")
        return    

    # Alert on the limits and conditions for the snooze and start of the flow of the complex snooze
    text = "Set a snooze until the BG level is higher then {} or below 140".format(high_border) if job_removed else "You not have any job runnig"
    await update.message.reply_text(text)
    context.job_queue.run_once(complx_snooze_is_in_condition, 1, chat_id=chat_id, name=str(chat_id), data=[high_border,update.message.chat_id])


async def simple_snooze(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Stopping the algorithm and running it in another 30 minutes"""
    chat_id = update.message.chat_id

    # If there is an active job (prediction algorithm) - delete it
    job_removed = remove_job_if_exists(str(chat_id), context)

    # Returning an answer to the user and adding a task of starting the predections algorithm in another 30 minutes
    text = "Set a snooze for 30 minutes" if job_removed else "You not have any job runnig"
    context.job_queue.run_repeating(start_pred_algorithm,  interval=60*2+30, first=30*60, chat_id=chat_id, name=str(chat_id))
    await update.message.reply_text(text)



async def last_5_bg(update: Update, context: ContextTypes.DEFAULT_TYPE,collection_mongo=collection_mongo) -> None:
    """Sending the user the last 5 BG values"""

    # If the user is not authorized, stop
    chat_id = update.effective_message.chat_id
    if chat_id not in ALLOWED_IDS:
        await update.effective_message.reply_text("You do not have permissions to perform this action")
        return

    last_5_bg = predKalman.currnet_bg_val(collection_mongo,5)
    text="Last 5 BG valeus are " + ', '.join(list(map(str, last_5_bg)))
    await update.message.reply_text(text)



async def next_bg(update: Update, context: ContextTypes.DEFAULT_TYPE,collection_mongo=collection_mongo) -> None:
    """Show the user the last 5 sugar values"""

    # If the user is not authorized, stop
    chat_id = update.effective_message.chat_id
    if chat_id not in ALLOWED_IDS:
        await update.effective_message.reply_text("You do not have permissions to perform this action")
        return
    
    # Conversion of values smaller than 40 to be "Low" - known convention
    predictions = predKalman.main_cgm(collection_mongo)
    predictions = ["Low" if predictions[i]<40 else predictions[i]  for i in range(3)]
    await update.message.reply_text(f"Next predictions is {', '.join(list(map(str, predictions[:3])))}")
    return



 ######################## RUNNING THE ALGORITHM ########################

def main() -> None:
    """Run bot"""

    # Create the Application and pass it your bot's token
    application = Application.builder().token(TOKEN).read_timeout(30).write_timeout(30).build()

    # on different commands - answer in Telegram
    application.add_handler(CommandHandler(["start","help"], help))
    application.add_handler(CommandHandler("start_predict", start_pred_algorithm))
    application.add_handler(CommandHandler("stop_predict", terminate_pred_algorithm ))
    application.add_handler(CommandHandler("simple_snooze", simple_snooze))
    application.add_handler(CommandHandler("complx_snooze", complx_snooze))
    application.add_handler(CommandHandler("next_bg", next_bg))
    application.add_handler(CommandHandler("last_5_bg", last_5_bg))


    # Run the bot
    print("boot is running")
    application.run_polling(timeout=600)


main()



