# creates snapshots via 'snapper'.
#
# Copyright (C) 2014 Igor Gnatenko
# Copyright (C) 2017 Red Hat
#
# This copyrighted material is made available to anyone wishing to use,
# modify, copy, or redistribute it subject to the terms and conditions of
# the GNU General Public License v.2, or (at your option) any later version.
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY expressed or implied, including the implied warranties of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General
# Public License for more details. You should have received a copy of the
# GNU General Public License along with this program; if not, write to the
# Free Software Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA
# 02110-1301, USA. Any Red Hat trademarks that are incorporated in the
# source code or documentation are not subject to the GNU General Public
# License and may only be used or replicated with the express permission of
# Red Hat, Inc.
#

from dbus import SystemBus, Interface, DBusException
import sys

from dnfpluginsextras import _, logger
import dnf


class Snapper(dnf.Plugin):
    name = 'snapper'

    def __init__(self, base, cli):
        self.base = base
        self.description = " ".join(sys.argv)
        self._snapper = None
        self._snapper_configs = {}

    def config(self):
        conf = self.read_config(self.base.conf)

        if conf.has_section("main"):
            if conf.has_option("main", "snapper_configs"):
                configs = conf.get("main", "snapper_configs").split()
                self._snapper_configs = dict.fromkeys(configs, None)
                logger.debug("snapper:" + _("configs: %s"), self._snapper_configs)

    def pre_transaction(self):
        if not self.base.transaction:
            return

        try:
            bus = SystemBus()
            self._snapper = Interface(bus.get_object('org.opensuse.Snapper',
                                      '/org/opensuse/Snapper'),
                                      dbus_interface='org.opensuse.Snapper')
        except DBusException as e:
            logger.critical(
                "snapper: " + _("connect to snapperd failed: %s"), e
            )
            return

        for config in self._snapper_configs.keys():
            try:
                logger.debug(
                    "snapper: " + _("creating pre_snapshot for %s"), config
                )
                pre_snap_number = self._snapper.CreatePreSnapshot(config,
                                                                  self.description,
                                                                  "number", {})
                self._snapper_configs[config] = pre_snap_number
                logger.debug(
                    "snapper: " + _("created pre_snapshot %d"), pre_snap_number
                )
            except DBusException as e:
                logger.critical(
                    "snapper: " + _("creating pre_snapshot failed: %s"), e
                )

    def transaction(self):
        if not self.base.transaction:
            return

        for (config, pre_snap_number) in self._snapper_configs.items():
            if pre_snap_number is None:
                logger.debug(
                    "snapper: " + _("skipping post_snapshot for %s because creation of pre_snapshot failed"), config
                )
                continue

            try:
                logger.debug(
                    "snapper: " + _("creating post_snapshot for %s")
                )
                snap_post_number = self._snapper.CreatePostSnapshot(config,
                                                                    pre_snap_number,
                                                                    self.description,
                                                                    "number", {})
                logger.debug(
                    "snapper: " + _("created post_snapshot %d"), snap_post_number
                )
            except DBusException as e:
                logger.critical(
                    "snapper: " + _("creating post_snapshot failed: %s"), e
                )
