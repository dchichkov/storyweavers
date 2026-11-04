#!/usr/bin/env python3
"""Local, dependency-free browser player. Bind only to the loopback interface."""
import argparse
from http.cookies import SimpleCookie
from http.server import BaseHTTPRequestHandler, HTTPServer
import json
from pathlib import Path
import secrets
import webbrowser

from engine import Session, replay

ROOT = Path(__file__).resolve().parent


def view(session):
    actions = session.actions() if not session.outcome else {}
    # Suggestions must not disclose the facts a player has yet to discover.
    known = session.state['people']['player']['knows']
    if not session.private_with:
        for action, fact in (('plan refund', 'refund'), ('plan visit', 'schedule')):
            if not known[fact]:
                actions.pop(action, None)
        for who in ('mara', 'eli'):
            if not session.state['people'][who]['disclosed']:
                actions.pop('reflect ' + who, None)
    return {'title': 'The Last Place Setting', 'seed': session.seed, 'turn': session.state['turn'],
            'location': session.state['people']['player']['location'], 'private_with': session.private_with,
            'outcome': session.outcome, 'actions': actions,
            'events': [{k: e[k] for k in ('id', 'turn', 'kind', 'source', 'lines')} for e in session.events],
            'known': [key for key, value in known.items() if value]}


class DramaServer(HTTPServer):
    def __init__(self, address, seed=0):
        super().__init__(address, Handler)
        self.seed = seed
        self.sessions = {}
        self.csrf = secrets.token_urlsafe(32)


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *_):
        pass

    def valid_host(self):
        return self.headers.get('Host') in ('127.0.0.1:' + str(self.server.server_port),
                                            'localhost:' + str(self.server.server_port))

    def get_session(self):
        cookie = SimpleCookie()
        try:
            cookie.load(self.headers.get('Cookie', ''))
        except Exception:
            pass
        token = cookie['drama_session'].value if 'drama_session' in cookie else None
        self.new_cookie = None
        if token not in self.server.sessions:
            # Bounded local browser sessions; oldest idle records may be exported first.
            if len(self.server.sessions) >= 32:
                self.server.sessions.pop(next(iter(self.server.sessions)))
            token = secrets.token_urlsafe(24)
            session = Session(self.server.seed)
            session.start()
            self.server.sessions[token] = session
            self.new_cookie = token
        self.session_token = token
        return self.server.sessions[token]

    def respond(self, value, status=200, content_type='application/json; charset=utf-8', attachment=None):
        body = value.encode('utf-8') if isinstance(value, str) else json.dumps(value, ensure_ascii=False).encode('utf-8')
        self.send_response(status)
        self.send_header('Content-Type', content_type)
        self.send_header('Content-Length', str(len(body)))
        self.send_header('Cache-Control', 'no-store')
        self.send_header('X-Content-Type-Options', 'nosniff')
        self.send_header('Content-Security-Policy', "default-src 'self'; style-src 'self' 'unsafe-inline'; script-src 'self' 'unsafe-inline'; frame-ancestors 'none'; base-uri 'none'")
        if getattr(self, 'new_cookie', None):
            self.send_header('Set-Cookie', 'drama_session=' + self.new_cookie + '; HttpOnly; SameSite=Strict; Path=/')
        if attachment:
            self.send_header('Content-Disposition', 'attachment; filename="' + attachment + '"')
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        if not self.valid_host():
            return self.respond({'error': 'Use the local URL printed by the server.'}, 403)
        session = self.get_session()
        if self.path == '/':
            return self.respond((ROOT / 'player.html').read_text(encoding='utf-8').replace('__CSRF__', self.server.csrf),
                                content_type='text/html; charset=utf-8')
        if self.path == '/api/state':
            return self.respond(view(session))
        if self.path == '/api/trace':
            return self.respond(session.export(), attachment='last-place-setting.json')
        if self.path == '/api/inspect':
            return self.respond({'world': session.snapshot(), 'director': session.selections[-6:],
                                 'completed': session.completed, 'aborted': session.aborted})
        return self.respond({'error': 'Not found'}, 404)

    def do_POST(self):
        if not self.valid_host() or self.headers.get('X-Drama-Token') != self.server.csrf:
            return self.respond({'error': 'This action must come from the local player.'}, 403)
        origin = self.headers.get('Origin')
        if origin and origin != 'http://' + self.headers.get('Host', ''):
            return self.respond({'error': 'Origin mismatch'}, 403)
        try:
            length = int(self.headers.get('Content-Length', '0'))
            if not 0 < length <= 4_000_000:
                raise ValueError('Invalid request size')
            data = json.loads(self.rfile.read(length))
            if not isinstance(data, dict):
                raise ValueError('Expected an object')
        except (ValueError, UnicodeError):
            return self.respond({'error': 'Could not read that request.'}, 400)
        session = self.get_session()
        if self.path == '/api/action':
            command = data.get('command')
            if not isinstance(command, str) or len(command) > 100:
                return self.respond({'error': 'Choose one of the available actions.'}, 400)
            if command not in session.actions() or session.outcome:
                return self.respond({'error': 'That action is not available here.'}, 409)
            session.step(command)
        elif self.path == '/api/new':
            seed = data.get('seed', self.server.seed)
            if not isinstance(seed, int) or isinstance(seed, bool) or not 0 <= seed <= 2**31:
                return self.respond({'error': 'Choose a seed between 0 and 2147483648.'}, 400)
            session = Session(seed)
            session.start()
            self.server.sessions[self.session_token] = session
        elif self.path == '/api/load':
            record = data.get('record')
            try:
                if not isinstance(record, dict) or not isinstance(record.get('commands'), list) or len(record['commands']) > 48:
                    raise ValueError('Invalid record')
                session = replay(record)
                if session.export() != record:
                    raise ValueError('The record does not match this version of the drama')
            except (KeyError, TypeError, ValueError, AttributeError, RuntimeError):
                return self.respond({'error': 'This record cannot be replayed exactly with this version.'}, 400)
            self.server.sessions[self.session_token] = session
        else:
            return self.respond({'error': 'Not found'}, 404)
        self.respond(view(session))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--port', type=int, default=8765)
    parser.add_argument('--seed', type=int, default=0)
    parser.add_argument('--open', action='store_true', help='Open your default browser')
    args = parser.parse_args()
    server = DramaServer(('127.0.0.1', args.port), args.seed)
    url = 'http://127.0.0.1:' + str(server.server_port)
    print('Play The Last Place Setting: ' + url, flush=True)
    print('Everything runs locally. Press Ctrl-C here to stop.', flush=True)
    if args.open:
        webbrowser.open(url)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == '__main__':
    main()
