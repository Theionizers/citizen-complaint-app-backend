
#include<bits/stdc++.h>
using namespace std;
int main(){
    int n=27;
    int s=0;
    int e=n;
    int ans;
    while(s<=e){
        int mid=(s+e)/2;
        //if(mid*mid==n)
        if(mid*mid<n){
    ans=mid;
         e=mid+1;


        }
        else {
            s=mid-1;
        }
    }
    cout<<ans;
}