
## Predicting Sugar Levels Using Kalman Filter- T1D


### **Preface**
The purpose of this project is to predict the sugar levels of people with juvenile diabetes (T1D) in order to provide an alert when there is a prediction that the sugar will go out of the desired range.

The project is intended for users who store their information in MongoDB, but with the necessary adjustments it can be adapted to other databases.


The project was carried out using Kalman filter based on the current sugar state and the change from the previous state. To read more about the [Kalman filter](https://en.wikipedia.org/wiki/Kalman_filter).

<div>
<img src="https://github.com/orineo1/predicting_sugar_level_T1D/blob/main/exampls/bot_init_gif.gif" width="400" height="700">
<img src="https://github.com/orineo1/predicting_sugar_level_T1D/blob/main/exampls/unwanted_bg_level_msg.jpeg" width="400" height="700">
</div>

### **Installation**
1. All files must be downloaded into one folder.
2. Telegram Bot must be set up according to Telegram's current guide ([possible guide](https://www.youtube.com/watch?v=NwBWW8cNCP4)).
3. Update of the desired values and data for the algorithm in the txt file - 'info_for_the_pred_algorithem.txt'.

>This information includes:
> 1. URI_MONGO, DB_NAME, COLLECTION_NAME - DB from which the information is drawn.
> 2. ALLOWED_IDS - Users who are allowed to run the application.
> 3. TOKEN - Token of the Telegram bot.
> 4. UPPER_BOUND, LOWER_BOUND, -  Desired sugar values  
> 5. Threshold_Alerts - Number of following different predictions* in which each one has at least one undesirable range which is required in order to trigger an alert.
>
> Note the data must be entered in separate lines directly after the "-"
>
>\* each predection includes 5 BG readings. 

4.  Finally enter to the CGMbot.py file and run it
5. That's it - the bot works and you can enter it in Telegram


### **Bot commands**

- **/start_predict** - Starts the prediction algorithm, by default when the prediction is out of range more than 3 times a message will be sent to the user. If there are more than 3 times out of range but the current prediction is all within the range, no message will be issued to the user.

- **/stop_predict** - Stops the prediction algorithm, and also stops any existing task in the algorithm.

- **/simple_snooze** - Stops notifications for 30 minutes.

- **/complx_snooze 'number'** -  Stops the notifications until reaching the 'number', intended for a situation where the sugar is stubborn and does not go down, but on the other hand it is not so high. The algorithm will work again if the current sugar is less than 140.

     <span style="text-decoration: underline">Without being modest, the complx_snooze is an excellent idea that should be applied to all the tools used to help with diabetes. It is more accurate for the users and I saw that my examinee was happy with it. </span>


- **/next_bg** - Gives the prediction for the next 3 readings.

- **/last_5_bg** - Gives the sugar values for the previous 5 readings.

- **/help /start** - Displays all information about all commands.

### **Summary**
It was a very fascinating project because on the one hand, it was to make a tool for a close person in order to improve their quality of life, and on the other hand, it was an opportunity to implement statistical and theoretical tools in practice.

I will point out that the tool is not state of the art. However, after testing it for days in relation to the tools that exist today, it showed pretty good predictions. A calculation of the MSE for the prediction success for the next 2 readings for a large sample of random data was approximately ~240 (I added a function to calcualte the MSE at the end of predictBGKalmnFilter.py).

**Plans for the future** -  improve the algorithm and instead of predicting the sugar levels using the change and the previous sugar levels, add to the Kalman Filter features like the amount of active carbohydrates in the body and the levels of active insulin. For this purpose, I thought of using a non-parametric regression and thereby estimating the weights of each of the different features.