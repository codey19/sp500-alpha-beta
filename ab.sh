## crontab entry, run every minute for testing purpose
## 
##  * * * * * /home/csheng/redvest/ab.sh
## 
cd /home/csheng/redvest
source redvest-env/bin/activate
/home/csheng/redvest/ab.py >> /home/csheng/redvest/ab.out
