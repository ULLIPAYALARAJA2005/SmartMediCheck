import pandas as pd 
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler
import pickle as pk


df=pd.read_csv("migraine.csv")
df1=df.drop(["Unnamed: 0"],axis=1)
x=df1.drop(["Type"],axis=1)
y=df1["Type"]
from sklearn.model_selection import train_test_split
x_train,x_test,y_train,y_test=train_test_split(x,y,test_size=0.1)
scaler=StandardScaler()
scaler.fit(x_train)
x_train_standardized=scaler.transform(x_train)
x_test_standardized=scaler.transform(x_test)
model=LogisticRegression()
model.fit(x_train_standardized,y_train)
model.predict(x_test_standardized)

pk.dump(model,open("migraine.pkl","wb"))
f=open("migraine.pkl","rb")
print(pk.load(f))
f.close()