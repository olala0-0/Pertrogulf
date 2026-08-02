# -*- coding: utf-8 -*-
from odoo import models, fields


class ContainerMaster(models.Model):
    _name = 'container.master'
    _description = 'Container Master'

    name = fields.Char(string="Container Type", required=True)
    description = fields.Char(string="Description")
    height = fields.Float(string="Height (ft)")
    width = fields.Float(string="Width (ft)")
    weight_capacity = fields.Float(string="Weight Capacity (kg)", required=True)
