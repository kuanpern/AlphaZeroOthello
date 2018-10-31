from flask import Flask
from flask_socketio import SocketIO, emit, join_room, leave_room
from flask import session, redirect, url_for, render_template, request, send_from_directory
from socket import *

socketio = SocketIO()
app = Flask(__name__)
socketio.init_app(app)


# fix this later
game_endpt = ("localhost", 5004)
UDPSock = socket(AF_INET, SOCK_DGRAM)

@app.route('/')
def index():
	return render_template('index.html')
# end def

@app.route('/js/<path:filename>')
def send_js(filename):
	return send_from_directory('js', filename)
# end def

@socketio.on('input_move', namespace='/console')
def input_move(data):
	UDPSock.sendto(str(data).encode(), game_endpt)
# end def


@socketio.on('draw_new_board', namespace='/console')
def text(message):
	emit('draw_new_board', message, broadcast=True)
# end def


######################################################
@socketio.on('R_log', namespace='/console')
def text(message):
	emit('R_log', message, broadcast=True)
# end def
######################################################


######################################################
@socketio.on('P_log', namespace='/console')
def text(message):
	print('received:', message)
	emit('P_log', message, broadcast=True)
# end def
######################################################


######################################################
@socketio.on('Q_log', namespace='/console')
def text(message):
	emit('Q_log', message, broadcast=True)
# end def
######################################################


######################################################
@socketio.on('put_confidence', namespace='/console')
def text(message):
	emit('put_confidence', message, broadcast=True)
# end def
######################################################









if __name__ == '__main__':
    socketio.run(app, port=8080, debug=True)
# end def
