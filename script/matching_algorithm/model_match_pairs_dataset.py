import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

import xgboost as xgb
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.linear_model import LinearRegression, Ridge
from sklearn.tree import DecisionTreeRegressor
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_percentage_error, mean_squared_error
from sklearn.preprocessing import StandardScaler

# from keras.models import Sequential
# from keras.layers import Dense
# from keras.optimizers import Adam

os.chdir(r"D:\GitHub\dilemma_zone")
df = pd.read_csv('data/match_training/matched_events_dataset.txt', sep = '\t')

X = df.drop('travel_time', axis = 1)
y = df.travel_time
rand_state = 1

# split train, test set
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size = 0.33, random_state = rand_state)

# =============================================================================
# EDA
# =============================================================================

# correlation between features
corr = df.corr()

# plot heatmap
fig = plt.figure()
ax = fig.add_subplot(111)
cax = ax.matshow(corr,cmap='coolwarm', vmin=-1, vmax=1)
fig.colorbar(cax)
ticks = np.arange(0,len(df.columns),1)
ax.set_xticks(ticks)
plt.xticks(rotation=90)
ax.set_yticks(ticks)
ax.set_xticklabels(df.columns)
ax.set_yticklabels(df.columns)
plt.show()

# =============================================================================
# Linear Regression
# =============================================================================

method = 'Linear Regression'
lr_reg = LinearRegression()

lr_reg.fit(X_train, y_train) # model fitting
y_pred = lr_reg.predict(X_test) # predicting

lr_mape = mean_absolute_percentage_error(y_test, y_pred)
lr_rmse = np.sqrt(mean_squared_error(y_test, y_pred))
r_squared = lr_reg.score(X_test, y_test)

print("MAPE for {}: {:.4f}".format(method, lr_mape))
print("RMSE for {}: {:.4f}".format(method, lr_rmse))
print("R squared for {}: {:.4f}".format(method, r_squared), "\n")

# =============================================================================
# Ridge Regression
# =============================================================================

method = 'Ridge Regression'
ridge_reg = Ridge(alpha = 0.5)

ridge_reg.fit(X_train, y_train) # model fitting
y_pred = ridge_reg.predict(X_test) # predicting

ridge_mape = mean_absolute_percentage_error(y_test, y_pred)
ridge_rmse = np.sqrt(mean_squared_error(y_test, y_pred))
r_squared = ridge_reg.score(X_test, y_test)

print("MAPE for {}: {:.4f}".format(method, ridge_mape))
print("RMSE for {}: {:.4f}".format(method, ridge_rmse))
print("R squared for {}: {:.4f}".format(method, r_squared), "\n")

# =============================================================================
# Decision Tree Regression
# =============================================================================

method = 'Decision Tree Regression'
dt_reg = DecisionTreeRegressor(criterion = 'mse', max_depth = 10, min_samples_split = 10)

dt_reg.fit(X_train, y_train) # model fitting
y_pred = dt_reg.predict(X_test) # predicting

dt_mape = mean_absolute_percentage_error(y_test, y_pred)
dt_rmse = np.sqrt(mean_squared_error(y_test, y_pred))

print("MAPE for {}: {:.4f}".format(method, dt_mape))
print("RMSE for {}: {:.4f}".format(method, dt_rmse), "\n")

# cross-validation
cross_val_score(dt_reg, X_train, y_train, cv = 10)

# =============================================================================
# Random Forest
# =============================================================================

method = 'Random Forest'
rf_reg = RandomForestRegressor()

rf_reg.fit(X_train, y_train) # model fitting
y_pred = rf_reg.predict(X_test) # predicting

rf_mape = mean_absolute_percentage_error(y_test, y_pred)
rf_rmse = np.sqrt(mean_squared_error(y_test, y_pred))

print("MAPE for {}: {:.4f}".format(method, rf_mape))
print("RMSE for {}: {:.4f}".format(method, rf_rmse), "\n")

# =============================================================================
# XGBoost
# =============================================================================

method = 'XGBoost'
xgb_reg = xgb.XGBRegressor(objective = 'reg:squarederror', random_state = rand_state)
 
xgb_reg.fit(X_train, y_train) # model fitting
y_pred = xgb_reg.predict(X_test) # predicting

xgb_mape = mean_absolute_percentage_error(y_test, y_pred)
xgb_rmse = np.sqrt(mean_squared_error(y_test, y_pred))

print("MAPE for {}: {:.4f}".format(method, xgb_mape))
print("RMSE for {}: {:.4f}".format(method, xgb_rmse), "\n")

# feature importance
feature_importances = xgb_reg.feature_importances_
    
# data frame of features and importances
importance_df = pd.DataFrame({'Feature': X.columns, 'Importance': feature_importances})
importance_df = importance_df.sort_values(by='Importance', ascending=False) # sorting

# plot feature importances
plt.figure(figsize=(10, 6))
plt.barh(importance_df['Feature'], importance_df['Importance'])
plt.xlabel('Feature Importance')
plt.ylabel('Feature')
plt.title('XGBoost Feature Importances')
plt.show()

# =============================================================================
# Wide and Deep Neural Network
# =============================================================================

# method = 'Wide and Deep Neural Network'

# # standardize features
# scaler = StandardScaler()
# X_train_scaled = scaler.fit_transform(X_train)
# X_test_scaled = scaler.transform(X_test)

# # create 'wide' part of neural network
# input_wide = Input(shape = (X_train_scaled.shape[1], ))
# wide_layer = Dense(32, activation = 'relu')(input_wide)

# # create 'deep' part of neural network
# input_deep = Input(shape = (X_train_scaled.shape[1], ))
# deep_layer = Dense(64, activation = 'relu')(input_deep)
# deep_layer = Dense(32, activation = 'relu')(deep_layer)

# # concatenate 'wide' and 'deep' parts
# concat_layer = Concatenate()([wide_layer, deep_layer])

# # add output layer with single neuron
# output_layer = Dense(1)(concat_layer)

# # create model
# model = Model(inputs = [input_wide, input_deep], outputs = output_layer)

# # compile model
# model.compile(optimizer = Adam(learning.rate = 0.001), loss = 'mean_absolute_percentage_error')
# model.summary()

# # train model
# model.fit([X_train_scaled, X_train_scaled], y_train, epochs = 50, batch_size = 32, validation_split = 0.1)

# # evaluate model on test set
# error = model.Evaluate([X_test_scaled, X_test_scaled], y_test)
# print("MAPE for {}: {:.4f}".format(method, error))
