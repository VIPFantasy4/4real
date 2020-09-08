# -*- coding: utf-8 -*-

import server.extraServerApi as serverApi
import cfg


class Srv(serverApi.GetServerSystemCls()):
    def Update(self):
        self._update()

    def Destroy(self):
        self.UnListenForEvent(serverApi.GetEngineNamespace(), serverApi.GetEngineSystemName(), 'AddServerPlayerEvent',
                              self, self.on_add)

        self._destroy()

    def __init__(self, *args):
        super(Srv, self).__init__(*args)
        self.ListenForEvent(serverApi.GetEngineNamespace(), serverApi.GetEngineSystemName(), 'AddServerPlayerEvent',
                            self, self.on_add)

        self._flag = 1

    def _update(self):
        pass

    def _destroy(self):
        pass

    def on_add(self, *args):
        print 'AddServerPlayerEvent'
