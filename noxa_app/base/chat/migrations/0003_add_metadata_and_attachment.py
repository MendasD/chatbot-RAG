from django.db import migrations, models
import django.db.models.deletion

class Migration(migrations.Migration):

    dependencies = [
        ('chat', '0002_chatattachment'),
    ]

    operations = [
        migrations.AddField(
            model_name='chatmessage',
            name='metadata',
            field=models.JSONField(blank=True, default=dict, help_text='Métadonnées extraites (questions suivies, images citées, etc.)'),
        ),
        migrations.AddField(
            model_name='chatsource',
            name='attachment',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='chat_references', to='chat.chatattachment'),
        ),
        migrations.AlterField(
            model_name='chatsource',
            name='publication',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='chat_references', to='base.publication'),
        ),
    ]
