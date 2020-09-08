# -*- coding: utf-8 -*-

from common.mod import Mod
import client.extraClientApi as clientApi
import cfg


@Mod.Binding(name=cfg.MOD_NAMESPACE, version=cfg.MOD_VER)
class RealMod(object):
    @Mod.InitClient()
    def _init(self):
        clientApi.RegisterSystem(cfg.MOD_NAMESPACE, cfg.MOD_CLI_NAME, cfg.MOD_CLI_CLASS)
