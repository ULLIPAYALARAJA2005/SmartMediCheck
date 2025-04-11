import pandas as pd 
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LogisticRegression
import pickle as pk


df=pd.read_csv("dengue.csv")
df1=df.drop(["Name"],axis=1)
x=df1.drop(["Dengue"],axis=1)
y=df1["Dengue"]

x_train,x_test,y_train,y_test=train_test_split(x,y,test_size=0.1)
model=LogisticRegression()
model.fit(x_train,y_train)

pk.dump(model,open("dengue.pkl","wb"))
f=open("dengue.pkl","rb")
print(pk.load(f))
f.close()