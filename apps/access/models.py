from django.db import models


class BusinessElement(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)

    class Meta:
        db_table = 'business_elements'

    def __str__(self):
        return self.name


class AccessRule(models.Model):
    role = models.ForeignKey('users.Role', on_delete=models.CASCADE, related_name='access_rules')
    element = models.ForeignKey(BusinessElement, on_delete=models.CASCADE, related_name='access_rules')
    read = models.BooleanField(default=False)
    read_all = models.BooleanField(default=False)
    create = models.BooleanField(default=False)
    update = models.BooleanField(default=False)
    update_all = models.BooleanField(default=False)
    delete = models.BooleanField(default=False)
    delete_all = models.BooleanField(default=False)

    class Meta:
        db_table = 'access_rules'
        unique_together = ('role', 'element')

    def __str__(self):
        return f'{self.role} → {self.element}'
