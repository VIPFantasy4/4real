# -*- coding: utf-8 -*-

import lobbyGame.netgameApi as onlineApi
import server.extraServerApi as serverApi
import cfg


class Srv(serverApi.GetServerSystemCls()):
    def Update(self):
        self._update()

    def Destroy(self):
        self.UnListenForEvent(serverApi.GetEngineNamespace(), serverApi.GetEngineSystemName(), 'AddServerPlayerEvent',
                              self, self.connection_made)
        self.UnListenForEvent(serverApi.GetEngineNamespace(), serverApi.GetEngineSystemName(),
                              'LoadServerAddonScriptsAfter', self, self.serve_forever)

        self._destroy()

    def __init__(self, *args):
        super(Srv, self).__init__(*args)
        self.ListenForEvent(serverApi.GetEngineNamespace(), serverApi.GetEngineSystemName(), 'AddServerPlayerEvent',
                            self, self.connection_made)
        self.ListenForEvent(serverApi.GetEngineNamespace(), serverApi.GetEngineSystemName(),
                            'LoadServerAddonScriptsAfter', self, self.serve_forever)

        self._flag = 1

    def _update(self):
        pass

    def _destroy(self):
        pass

    def serve_forever(self, *args):
        pass

    def connection_made(self, data):
        uid = onlineApi.GetPlayerUid(data.get('id'))
        if not uid:
            return
