# -*- coding: utf-8 -*-

import client.extraClientApi as clientApi
import cfg


class Cli(clientApi.GetClientSystemCls()):
    def Update(self):
        self._update()

    def Destroy(self):
        self.UnListenForEvent(clientApi.GetEngineNamespace(), clientApi.GetEngineSystemName(), 'UiInitFinished', self,
                              self.on_ui_init_finished)

        self._destroy()

    def __init__(self, *args):
        super(Cli, self).__init__(*args)
        self.ListenForEvent(clientApi.GetEngineNamespace(), clientApi.GetEngineSystemName(), 'UiInitFinished', self,
                            self.on_ui_init_finished)

        self._flag = 1

    def _update(self):
        pass

    def _destroy(self):
        pass

    def on_ui_init_finished(self, *args):
        clientApi.RegisterUI(cfg.MOD_NAMESPACE, cfg.UI_NAMESPACE, cfg.UI_CLASS, cfg.UI_MAIN)
        clientApi.CreateUI(cfg.MOD_NAMESPACE, cfg.UI_NAMESPACE, {"isHud": 0})


class GUI(clientApi.GetScreenNodeCls()):
    def Create(self):
        print 'create gui'

    def __init__(self, *args):
        super(GUI, self).__init__(*args)
