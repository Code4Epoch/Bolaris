from live import live_data_summary
from live import tool_function as tf


room_id, live_date, live_road, live_type = tf.get_arg()

live = live_data_summary.live_summary(my_room_id=room_id, my_live_date=live_date,
                                      my_live_road=live_road, my_live_type=live_type)
live.get_everyday_live_stats()
