
## Predicting Sugar Level Using Kalman Filter- T1D


### preface
The purpose of this project is to predict the sugar status in people with juvenile diabetes (T1D) in order to provide an alert when there is a prediction that the sugar will go out of the desired range.

The project is intended for users who store their information in MongoDB, but with the necessary adjustments it can be adapted to other databases.


The project was carried out mostly based on a Kalman filter based on the current sugar state and the change from the previous state. To read more about the [Kalman filter](https://en.wikipedia.org/wiki/Kalman_filter).

### installation
1. All files must be downloaded into one folder.
2. Telegram Bot must be set up according to Telegram's current guide ([possible guide](https://www.youtube.com/watch?v=NwBWW8cNCP4)).
3. Update of the desired values and data for the algorithm in the txt file - 'info_for_the_pred_algorithem.txt'

>This information includes:
> 1. URI_MONGO, DB_NAME, COLLECTION_NAME - DB from which the information is drawn
> 2. ALLOWED_IDS - Users who are allowed to run the application
> 3. TOKEN - Token of the Telegram bot
> 4. UPPER_BOUND, LOWER_BOUND, Threshold_Alerts-  Desired sugar values and the number of predictions in an undesirable range required in order to trigger an alert.
>
>Note The data must be entered in separate lines directly after the "-"

4.  Finally enter to the CGMbot.py file and run it
5. That's it - the bot works and you can enter it in Telegram


### Bot commands

- **/start_predict** - Start of the prediction algorithm, by default when the prediction is out of range more than 3 times a message will be sent to the user. If there are more than 3 times out of range but the current prediction is all within the range, no message will be issued to the user.

- **/stop_predict** - Stops the prediction algorithm, and also stops any existing task in the algorithm.

- **/simple_snooze** - Stops notifications for 30 minutes.

- **/complx_snooze 'number'** -  Stops the notifications until reaching the 'number', intended for a situation where the sugar is stubborn and does not go down, but on the other hand it is not so high. The algorithm will work again if the current sugar is less than 140.

    <span style ="color:green">Without being modest, the complx_snooze is an excellent idea that should be applied to all the tools used to help with diabetes. Accurate for the users and I saw that my examinee was happy with it.<span>


- **/next_5_bg** - Gives the prediction for the next 5 readings.

- **/last_5_bg** - Gives the sugar values for the previous 5 readings.

- **/help** - Displays all information about all commands.

### Summary
It was a very fascinating project, on the one hand to make a tool for a close person in order to improve his quality of life and on the other hand to implement statistical and theoretical tools in practice.

I will point out that the tool is not state of the art, but it shows not bad predictions at all After testing it for days in relation to the tools that exist today. A calculation of the MSE for the prediction success for the next 2 readings for a large sample of random data was approximately ~309. 

**Plans for the future** -  improve the algorithm and instead of predicting the sugar levels using the change and the previous sugar level, add to the Kalman Filter also the use of features of the amount of active carbohydrates in the blood and the levels of active insulin. For this purpose, I thought of using a non-parametric regression and thereby estimating the weights of each of the different features.