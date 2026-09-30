import sys, json

with open('/tmp/mcp_probe.log', 'w') as log:
    log.write('STARTED\n')
    log.flush()
    while True:
        line = sys.stdin.readline()
        if not line:
            break
        log.write('RECV: ' + line)
        log.flush()
        try:
            msg = json.loads(line)
            mid = msg.get('id')
            method = msg.get('method')
            if method == 'server/discover':
                resp = {'jsonrpc': '2.0', 'id': mid, 'error': {'code': -32601, 'message': 'Method not found'}}
            elif method == 'initialize':
                resp = {
                    'jsonrpc': '2.0',
                    'id': mid,
                    'result': {
                        'protocolVersion': '2024-11-05',
                        'capabilities': {'tools': {}},
                        'serverInfo': {'name': 'cleanops-mcp', 'version': '1.0.0'}
                    }
                }
            elif method == 'tools/list':
                resp = {
                    'jsonrpc': '2.0',
                    'id': mid,
                    'result': {
                        'tools': [{
                            'name': 'cleanops_ping',
                            'description': 'Ping CleanOps test tool',
                            'inputSchema': {
                                'type': 'object',
                                'properties': {
                                    'msg': {'type': 'string', 'description': 'A test message'}
                                },
                                'required': ['msg']
                            }
                        }]
                    }
                }
            elif method == 'tools/call':
                resp = {
                    'jsonrpc': '2.0',
                    'id': mid,
                    'result': {
                        'content': [{'type': 'text', 'text': 'PONG from CleanOps MCP!'}]
                    }
                }
            elif mid is not None:
                resp = {'jsonrpc': '2.0', 'id': mid, 'result': {}}
            else:
                resp = None

            if resp is not None:
                out = json.dumps(resp) + '\n'
                sys.stdout.write(out)
                sys.stdout.flush()
                log.write('SENT: ' + out)
                log.flush()
        except Exception as e:
            log.write('ERR: ' + str(e) + '\n')
            log.flush()
