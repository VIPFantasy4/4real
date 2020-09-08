# -*- coding: utf-8 -*-

from common.mod import Mod
import server.extraServerApi as serverApi
import cfg


@Mod.Binding(name=cfg.MOD_NAMESPACE, version=cfg.MOD_VER)
class RealMod(object):
    @Mod.InitServer()
    def _init(self):
        serverApi.RegisterSystem(cfg.MOD_NAMESPACE, cfg.MOD_SRV_NAME, cfg.MOD_SRV_CLASS)
