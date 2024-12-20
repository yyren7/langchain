
   def connect_robot():
       ip = "192.168.250.101"
       dashboard_port = 29999
       move_port = 30003
       feed_port = 30004

       dashboard = DobotApiDashboard(ip, dashboard_port)
       move = DobotApiMove(ip, move_port)
       feed = DobotApi(ip, feed_port)

       return dashboard, move, feed
   