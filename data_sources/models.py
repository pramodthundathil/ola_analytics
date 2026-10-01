from django.db import models


class DataSource(models.Model):
    TYPE_CHOICES = (
        ("MONGODB", "MongoDB (OlaCarsBackend ERP)"),
        ("POSTGRESQL", "PostgreSQL"),
        ("MYSQL", "MySQL"),
        ("SQLITE", "SQLite"),
    )

    name = models.CharField(max_length=100, unique=True, help_text="Data source display name")
    db_type = models.CharField(max_length=20, choices=TYPE_CHOICES, default="MONGODB")
    host = models.CharField(max_length=255, blank=True, null=True)
    port = models.IntegerField(blank=True, null=True)
    database_name = models.CharField(max_length=100)
    username = models.CharField(max_length=100, blank=True, null=True, help_text="Read-only user e.g. ola_ai_readonly")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name} ({self.db_type})"


class TableMetadata(models.Model):
    data_source = models.ForeignKey(DataSource, on_delete=models.CASCADE, related_name="tables")
    table_name = models.CharField(max_length=100, help_text="Exact collection or table name in database")
    display_name = models.CharField(max_length=100)
    description = models.TextField(blank=True, help_text="Business explanation of what this entity represents")
    is_sensitive = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("data_source", "table_name")

    def __str__(self):
        return f"{self.data_source.name} -> {self.table_name}"


class ColumnMetadata(models.Model):
    table = models.ForeignKey(TableMetadata, on_delete=models.CASCADE, related_name="columns")
    column_name = models.CharField(max_length=100)
    data_type = models.CharField(max_length=50)
    business_meaning = models.TextField(blank=True, help_text="Plain text description for AI query generator")
    is_primary_key = models.BooleanField(default=False)
    is_foreign_key = models.BooleanField(default=False)
    foreign_table = models.CharField(max_length=100, blank=True, null=True)

    def __str__(self):
        return f"{self.table.table_name}.{self.column_name}"


class MetricDefinition(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField()
    category = models.CharField(max_length=50, choices=(
        ("REVENUE", "Revenue"),
        ("BOOKINGS", "Bookings"),
        ("FLEET", "Fleet"),
        ("CUSTOMERS", "Customers"),
        ("FINANCIAL", "Financial"),
    ), default="REVENUE")
    sql_formula = models.TextField(help_text="Pre-validated SQL/MongoDB query formula for this metric")
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"[{self.category}] {self.name}"
