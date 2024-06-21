import logging

from apps.smurfen.dbcleanup.views import CleanupMapListView
from pyplanet.apps.config import AppConfig
from pyplanet.apps.core.maniaplanet.models import Map
from pyplanet.contrib.command import Command
from pyplanet.apps.contrib.karma.models.karma import Karma
from pyplanet.apps.contrib.local_records.models.local_record import LocalRecord
from pyplanet.apps.contrib.jukebox.models.mapfolder import MapInFolder
from pyplanet.apps.core.statistics.models import Score


class DatabaseCleanup(AppConfig):
	game_dependencies = ['trackmania']
	app_dependencies = ['core.maniaplanet', 'core.trackmania']

	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)

	async def on_start(self):
		await self.instance.permission_manager.register('dbcleanup', 'Database clean-up', app=self, min_level=3)
		await self.instance.command_manager.register(Command(command='clean', namespace=['database', 'db'], target=self.command_database_cleanup, perms='dbcleanup:dbcleanup', admin=True))

	async def command_database_cleanup(self, player, data, **kwargs):
		server_maps = self.instance.map_manager.maps
		server_map_uids = [map.uid for map in server_maps]
		old_database_maps = await Map.objects.execute(Map.select().where(Map.uid.not_in(server_map_uids)))
		old_database_map_uids = [old_database_map.uid for old_database_map in old_database_maps]

		logging.info('[DBCleanup] Clean-up initiated by {}'.format(player.login))
		logging.info('[DBCleanup] Maps on the server: {}'.format(len(server_maps)))
		logging.info('[DBCleanup] Old maps in database: {}'.format(len(old_database_maps)))

		logging.info('[DBCleanup] Old maps to be cleaned: {}'.format(len(old_database_maps)))

		if len(old_database_maps) > 0:
			view = CleanupMapListView(self, old_database_maps)
			await view.display(player)
		else:
			message = '$f00$iThere are no maps to be cleaned from the database.'
			await self.instance.chat(message, player.login)

	async def confirm_clean(self, player, maps):
		logging.info('[DBCleanup] Confirmed cleaning of {} maps by {}.'.format(len(maps), player.login))
		start_message = '$a94Map clean-up started by $fff{}$z$s$a94, progress will be reported here.'.format(player.nickname)
		await self.inform_admins(start_message)

		# Delete the maps in chunks to avoid overloading the database.
		chunk_size = 50
		total_maps_deleted = 0
		map_chunks = [maps[i * chunk_size:(i + 1) * chunk_size] for i in range((len(maps) + chunk_size - 1) // chunk_size)]
		logging.info('[DBCleanup] Created chunks (of max. 20 maps): {}'.format(len(map_chunks)))

		for chunk_nr in range(0, len(map_chunks)):
			logging.info('[DBCleanup] Chunk {} / {}'.format((chunk_nr + 1), len(map_chunks)))

			map_chunk = map_chunks[chunk_nr]
			map_chunk_ids = [map.id for map in map_chunk]
			karma_deleted = await Karma.objects.execute(Karma.delete().where(Karma.map_id.in_(map_chunk_ids)))
			records_deleted = await LocalRecord.objects.execute(LocalRecord.delete().where(LocalRecord.map_id.in_(map_chunk_ids)))
			mapinfolder_deleted = await MapInFolder.objects.execute(MapInFolder.delete().where(MapInFolder.map_id.in_(map_chunk_ids)))
			scores_deleted = await Score.objects.execute(Score.delete().where(Score.map_id.in_(map_chunk_ids)))
			map_deleted = await Map.objects.execute(Map.delete().where(Map.id.in_(map_chunk_ids)))

			logging.info('[DBCleanup] Chunk {}: map ids = {}'.format((chunk_nr + 1), map_chunk_ids))
			logging.info('[DBCleanup] Chunk {}: karma votes deleted = {}'.format((chunk_nr + 1), karma_deleted))
			logging.info('[DBCleanup] Chunk {}: local records deleted = {}'.format((chunk_nr + 1), records_deleted))
			logging.info('[DBCleanup] Chunk {}: map in folder deleted = {}'.format((chunk_nr + 1), mapinfolder_deleted))
			logging.info('[DBCleanup] Chunk {}: scores deleted = {}'.format((chunk_nr + 1), scores_deleted))
			logging.info('[DBCleanup] Chunk {}: maps deleted = {}'.format((chunk_nr + 1), map_deleted))

			total_maps_deleted += map_deleted
			message = '$a94Maps cleaned: $fff{}$a94/$fff{}$a94 (this chunk: $fff{}$a94 karma, $fff{}$a94 records, $fff{}$a94 scores).'.format(
				total_maps_deleted, len(maps), karma_deleted, records_deleted, scores_deleted)
			await self.inform_admins(message)

	async def inform_admins(self, message):
		for player in self.instance.player_manager.online:
			if await self.instance.permission_manager.has_permission(player, 'dbcleanup:dbcleanup'):
				await self.instance.chat(message, player.login)
