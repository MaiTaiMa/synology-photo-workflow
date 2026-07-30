"""Projekt: Synology Photo Workflow
Datei: tests/conftest.py
Mitentwickler: MaiTai
Erstellt: 2026-07-29
Projektversion: 7.7.0
Funktion: Synthetische, private-freie NAS-Testumgebung und Konfigurationsfixture.
"""
from pathlib import Path
import yaml


def write_config(tmp_path, **overrides):
    cfg={
      'paths': {'basedir':str(tmp_path),'temp_sd':'TEMP_SD','temp_images':'TEMP_IMAGES','temp_done':'TEMP_DONE','temp_error':'TEMP_ERROR','workflow_data':'WORKFLOW_DATA','manual_keep_inbox':'MANUAL_KEEP/inbox','manual_keep_used':'MANUAL_KEEP/used'},
      'workflow': {'phase_execution':'phase1_then_phase2','batch_limit':1,'batch_sort':'oldest_first','skip_incomplete_batches':False,'max_run_hours':10,'resume_incomplete_batches':True,'dry_run':False},
      'culling': {'enabled':True,'keep_threshold':.65,'reject_threshold':.35,'auto_keep_min_rating':2,'final_component_weights':{'base_score':.55,'eye_score':.1,'personal_score':.2,'family_score':.15},'base_weights':{'sharpness':.35,'aesthetic':.35,'exposure':.2,'reference_score':.1},'star_rating_bands':[{'min':0,'max':.19,'rating':0},{'min':.2,'max':.39,'rating':1},{'min':.4,'max':.59,'rating':2},{'min':.6,'max':.74,'rating':3},{'min':.75,'max':.89,'rating':4},{'min':.9,'max':1,'rating':5}]},
      'phase2':{'delete_unneeded_arws_after_verified_archive':True,'allow_automatic_handoff':False},
      'metadata':{'write_mode':'disabled','verify_after_write':True,'create_exiftool_backups':False,'sidecar_recovery_enabled':False},
      'family_recognition':{'enabled':False,'backend':'opencv_yunet_sface_cpu','execution_profile':'cpu','metric':'cosine_similarity','match_threshold':None,'min_best_second_margin':None,'backends':{}},
      'automation':{'mode':'assisted_review','automatic_phase2_enabled':False,'automatic_candidates_enabled':False,'automatic_reference_activation':False,'automatic_sample_activation':False,'rollback_on_error':True},
      'calibration':{'enabled':True,'reviewed_batches_minimum':3,'reviewed_images_minimum':300,'terminal_agreement_minimum':.9,'reject_to_keep_rate_maximum':0,'shadow_model_enabled':False}}
    for section, values in overrides.items(): cfg[section].update(values)
    p=Path(tmp_path)/'config.yaml';p.write_text(yaml.safe_dump(cfg),encoding='utf-8');return p
