from playhouse.shortcuts import model_to_dict

from pyplanet.apps.core.maniaplanet.models import Map
from pyplanet.views.generics import ask_confirmation
from pyplanet.views.generics.list import ManualListView


class CleanupMapListView(ManualListView):
	model = Map
	title = 'Maps to be cleaned from database'
	icon_style = 'Icons128x128_1'
	icon_substyle = 'Browse'

	old_database_maps = list()

	def __init__(self, app, old_database_maps):
		super().__init__(self)
		self.app = app
		self.manager = app.context.ui
		self.old_database_maps = old_database_maps

	async def get_data(self):
		data = list()
		for m in self.old_database_maps:
			data.append(model_to_dict(m))
		return data

	async def get_fields(self):
		return [
			{
				'name': 'Name',
				'index': 'name',
				'sorting': True,
				'searching': True,
				'width': 80,
				'type': 'label'
			},
			{
				'name': 'Author',
				'index': 'author_login',
				'sorting': True,
				'searching': True,
				'renderer': lambda row, field:
				row['author_nickname']
				if 'author_nickname' in row and row['author_nickname'] and len(row['author_nickname'])
				else row['author_login'],
				'width': 50,
			},
			{
				'name': 'Added at',
				'index': 'created_at',
				'sorting': True,
				'searching': True,
				'width': 40,
				'type': 'label'
			},
			{
				'name': 'Last updated at',
				'index': 'updated_at',
				'sorting': True,
				'searching': True,
				'width': 40,
				'type': 'label'
			},
		]

	async def get_buttons(self):
		buttons = [
			{
				'title': 'Clean!',
				'width': 20,
				'action': self.action_clean
			}
		]

		return buttons

	async def action_clean(self, player, values, **kwargs):
		cancel = await ask_confirmation(player, 'Are you sure you want to clean {} maps in the database? Active maps and old SmurfsCup maps are NOT included. This might take a while and is irreversible!'.format(
			len(self.old_database_maps), (len(self.old_database_maps) + len(self.app.instance.map_manager.maps))), size='sm')

		await self.close(player)

		if not cancel:
			await self.app.confirm_clean(player, self.old_database_maps)
