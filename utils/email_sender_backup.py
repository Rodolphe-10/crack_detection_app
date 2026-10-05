"""
Utilitaires pour l'envoi d'emails avec rapports d'analyse
"""

import smtplib
import os
import streamlit as st
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from pathlib import Path
import tempfile
from datetime import datetime
from typing import List, Dict, Optional, Tuple
import zipfile

from config.config import EmailConfig, NotificationConfig


class EmailSender:
    """Gestionnaire d'envoi d'emails pour les rapports d'analyse."""
    
    def __init__(self):
        """Initialise le gestionnaire d'email."""
        self.config = EmailConfig()
        self.notification_config = NotificationConfig()
        
        # Configuration SMTP depuis les secrets ou variables d'environnement
        self.smtp_email = self._get_smtp_credential('SMTP_EMAIL')
        self.smtp_password = self._get_smtp_credential('SMTP_PASSWORD')
        self.smtp_server = self._get_smtp_credential('SMTP_SERVER', EmailConfig.SMTP_SERVER)
        self.smtp_port = int(self._get_smtp_credential('SMTP_PORT', str(EmailConfig.SMTP_PORT)))
    
    def _get_smtp_credential(self, key: str, default: str = '') -> str:
        """Récupère les credentials SMTP depuis les secrets ou environnement.
        Utilise l'API recommandée de Streamlit pour éviter les faux négatifs.
        """
        try:
            # Secrets Streamlit (accès type dict recommandé)
            if key in st.secrets:
                return str(st.secrets[key])
            
            # Vérifier dans la section [email] si la clé n'est pas trouvée à la racine
            if hasattr(st.secrets, 'email') and key in st.secrets.email:
                return str(st.secrets.email[key])
                
            # Mapping des clés pour la compatibilité
            key_mapping = {
                'SMTP_EMAIL': 'SMTP_USERNAME',
                'SMTP_PASSWORD': 'SMTP_PASSWORD',
                'SMTP_SERVER': 'SMTP_SERVER',
                'SMTP_PORT': 'SMTP_PORT'
            }
            
            if key in key_mapping and hasattr(st.secrets, 'email'):
                mapped_key = key_mapping[key]
                if mapped_key in st.secrets.email:
                    return str(st.secrets.email[mapped_key])
                    
        except Exception:
            pass
        # Variables d'environnement en fallback
        return os.getenv(key, default)
    
    def is_configured(self) -> bool:
        """Vérifie si l'envoi d'email est configuré."""
        return bool(self.smtp_email and self.smtp_password)
    
    def validate_email(self, email: str) -> bool:
        """Valide le format d'une adresse email."""
        import re
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(pattern, email) is not None
    
    def create_analysis_summary(self, analysis_results: Dict) -> str:
        """Crée un résumé de l'analyse pour l'email."""
        summary_lines = []
        
        # Type d'analyse
        analysis_type = analysis_results.get('type', 'Simple')
        summary_lines.append(f"🔍 Type d'analyse: {analysis_type}")
        
        # Date/heure
        timestamp = analysis_results.get('timestamp', datetime.now().strftime('%d/%m/%Y %H:%M'))
        summary_lines.append(f"📅 Date: {timestamp}")
        
        # Résultats principaux
        if 'classification' in analysis_results:
            has_crack = analysis_results['classification'].get('has_crack', False)
            confidence = analysis_results['classification'].get('confidence', 0)
            
            if has_crack:
                summary_lines.append(f"⚠️ Résultat: FISSURE DÉTECTÉE (Confiance: {confidence:.1%})")
            else:
                summary_lines.append(f"✅ Résultat: STRUCTURE SAINE (Confiance: {confidence:.1%})")
        
        # Métriques de segmentation
        if 'segmentation' in analysis_results:
            seg_metrics = analysis_results['segmentation']
            if 'surface_area' in seg_metrics:
                summary_lines.append(f"📊 Surface fissurée: {seg_metrics['surface_area']:.1f} mm²")
            if 'crack_density' in seg_metrics:
                summary_lines.append(f"📈 Densité: {seg_metrics['crack_density']:.2f}%")
        
        # Statistiques batch
        if 'batch_stats' in analysis_results:
            stats = analysis_results['batch_stats']
            summary_lines.append(f"📊 Images analysées: {stats.get('total_images', 0)}")
            summary_lines.append(f"⚠️ Fissures détectées: {stats.get('cracked_images', 0)}")
            summary_lines.append(f"✅ Structures saines: {stats.get('healthy_images', 0)}")
        
        return "\n    ".join(summary_lines)
    
    def create_attachments_list(self, attachments: List[str]) -> str:
        """Crée la liste des pièces jointes pour l'email."""
        if not attachments:
            return "Aucune pièce jointe"
        
        attachment_lines = []
        for attachment in attachments:
            filename = Path(attachment).name
            size_mb = Path(attachment).stat().st_size / (1024 * 1024)
            attachment_lines.append(f"📄 {filename} ({size_mb:.1f} MB)")
        
        return "\n    ".join(attachment_lines)
    
    def compress_large_attachments(self, attachments: List[str]) -> Tuple[List[str], float]:
        """Compresse les pièces jointes si nécessaire."""
        total_size = sum(Path(f).stat().st_size for f in attachments) / (1024 * 1024)
        
        if total_size <= self.config.MAX_ATTACHMENT_SIZE_MB:
            return attachments, total_size
        
        # Créer une archive ZIP
        with tempfile.NamedTemporaryFile(suffix='.zip', delete=False) as temp_zip:
            with zipfile.ZipFile(temp_zip.name, 'w', zipfile.ZIP_DEFLATED) as zipf:
                for attachment in attachments:
                    zipf.write(attachment, Path(attachment).name)
            
            zip_size = Path(temp_zip.name).stat().st_size / (1024 * 1024)
            return [temp_zip.name], zip_size
    
    def send_analysis_report(
        self, 
        recipient_email: str,
        analysis_results: Dict,
        attachments: Optional[List[str]] = None,
        custom_message: str = "",
        subject_override: Optional[str] = None,
    ) -> Tuple[bool, str]:
        """
        Envoie un rapport d'analyse par email.
        
        Args:
            recipient_email: Email du destinataire
            analysis_results: Résultats de l'analyse
            attachments: Liste des fichiers à joindre
            custom_message: Message personnalisé
            
        Returns:
            Tuple (success, message)
        """
        try:
            # Vérifications préliminaires
            if not self.is_configured():
                return False, "❌ Configuration email manquante (SMTP_EMAIL/SMTP_PASSWORD)"
            
            if not self.validate_email(recipient_email):
                return False, f"❌ Adresse email invalide: {recipient_email}"
            
            # Préparer les pièces jointes
            attachments = attachments or []
            processed_attachments, total_size = self.compress_large_attachments(attachments)
            
            if total_size > self.config.MAX_ATTACHMENT_SIZE_MB:
                return False, f"❌ Pièces jointes trop volumineuses ({total_size:.1f} MB > {self.config.MAX_ATTACHMENT_SIZE_MB} MB)"
            
            # Déterminer le type d'email
            analysis_type = analysis_results.get('type', 'single').lower()
            subject_key = f'subject_{analysis_type}'
            default_subject = self.config.EMAIL_TEMPLATES.get(
                subject_key, self.config.EMAIL_TEMPLATES['subject_single']
            )
            subject = subject_override or default_subject
            
            # Créer le contenu de l'email
            summary = self.create_analysis_summary(analysis_results)
            attachments_list = self.create_attachments_list(processed_attachments)
            
            body = self.config.EMAIL_BODY_TEMPLATE.format(
                summary=summary,
                attachments=attachments_list
            )
            
            if custom_message:
                body = f"{custom_message}\n\n{body}"
            
            # Créer le message MIME
            msg = MIMEMultipart()
            msg['From'] = self.smtp_email
            msg['To'] = recipient_email
            msg['Subject'] = subject
            
            # Ajouter le corps du message
            msg.attach(MIMEText(body, 'plain', 'utf-8'))
            
            # Ajouter les pièces jointes
            for attachment_path in processed_attachments:
                with open(attachment_path, "rb") as attachment:
                    part = MIMEBase('application', 'octet-stream')
                    part.set_payload(attachment.read())
                
                encoders.encode_base64(part)
                filename = Path(attachment_path).name
                part.add_header(
                    'Content-Disposition',
                    f'attachment; filename= {filename}'
                )
                msg.attach(part)
            
            # Envoyer l'email avec négociation TLS/SSL appropriée
            if self.smtp_port == 465:
                server = smtplib.SMTP_SSL(self.smtp_server, self.smtp_port)
            else:
                server = smtplib.SMTP(self.smtp_server, self.smtp_port)
                server.ehlo()
                if EmailConfig.USE_TLS:
                    server.starttls()
                    server.ehlo()
            server.login(self.smtp_email, self.smtp_password)
            text = msg.as_string()
            server.sendmail(self.smtp_email, recipient_email, text)
            server.quit()
            
            # Nettoyer les fichiers temporaires (ZIP)
            for attachment in processed_attachments:
                if attachment.endswith('.zip') and attachment not in (attachments or []):
                    Path(attachment).unlink(missing_ok=True)
            
            return True, f"✅ Email envoyé avec succès à {recipient_email}"
            
        except smtplib.SMTPAuthenticationError:
            return False, "❌ Erreur d'authentification SMTP - Vérifiez vos identifiants"
        except smtplib.SMTPServerDisconnected:
            return False, "❌ Erreur de connexion au serveur SMTP"
        except smtplib.SMTPException as e:
            return False, f"❌ Erreur SMTP: {str(e)}"
        except Exception as e:
            return False, f"❌ Erreur inattendue: {str(e)}"


class EmailInterface:
    """Interface Streamlit pour l'envoi d'emails."""
    
    def __init__(self):
        self.sender = EmailSender()
    
    def _test_smtp_connection(self) -> Tuple[bool, str]:
        """Teste la connexion SMTP et l'authentification."""
        try:
            if self.sender.smtp_port == 465:
                server = smtplib.SMTP_SSL(self.sender.smtp_server, self.sender.smtp_port)
            else:
                server = smtplib.SMTP(self.sender.smtp_server, self.sender.smtp_port)
                server.ehlo()
                if EmailConfig.USE_TLS:
                    server.starttls()
                    server.ehlo()
            server.login(self.sender.smtp_email, self.sender.smtp_password)
            server.quit()
            return True, "✅ Connexion SMTP et authentification OK"
        except smtplib.SMTPAuthenticationError:
            return False, "❌ Authentification SMTP échouée (identifiants)"
        except smtplib.SMTPServerDisconnected:
            return False, "❌ Déconnexion/connexion serveur SMTP"
        except smtplib.SMTPException as e:
            return False, f"❌ Erreur SMTP: {str(e)}"
        except Exception as e:
            return False, f"❌ Erreur inattendue: {str(e)}"
    
    def show_email_configuration_status(self):
        """Affiche le statut de la configuration email."""
        if self.sender.is_configured():
            st.success("✅ Configuration email disponible")
            st.info(f"📧 Serveur: {self.sender.smtp_server}:{self.sender.smtp_port}")
            st.info(f"👤 Compte: {self.sender.smtp_email}")
        else:
            st.info("ℹ️ Configuration email non configurée")
            with st.expander("🔧 Instructions de configuration"):
                st.markdown("""
                **Pour activer l'envoi d'emails, configurez :**
                
                1. **Dans secrets.toml** (recommandé) :
                ```toml
                SMTP_EMAIL = "votre-email@gmail.com"
                SMTP_PASSWORD = "votre-mot-de-passe-app"
                SMTP_SERVER = "smtp.gmail.com"
                SMTP_PORT = "587"
                ```
                
                2. **Ou variables d'environnement** :
                - `SMTP_EMAIL`
                - `SMTP_PASSWORD` 
                - `SMTP_SERVER` (optionnel)
                - `SMTP_PORT` (optionnel)
                
                **⚠️ Important :** Pour Gmail, utilisez un mot de passe d'application
                """)
    
    def show_send_email_interface(
        self, 
        analysis_results: Dict, 
        attachments: Optional[List[str]] = None,
        default_email: str = ""
    ):
        """
        Affiche l'interface d'envoi d'email.
        
        Args:
            analysis_results: Résultats de l'analyse
            attachments: Fichiers à joindre
            default_email: Email par défaut
        """
        # Interface épurée: pas de section de configuration ici
        st.markdown("### 📧 Envoyer le Rapport par Email")
        
        # Formulaire d'envoi
        with st.form("send_report_form"):
            col1, col2 = st.columns([2, 1])
            with col1:
                recipient_email = st.text_input(
                    "📧 Adresse email du destinataire",
                    value=default_email,
                    placeholder="exemple@entreprise.com",
                    help="Saisissez l'adresse email du destinataire"
                )
            with col2:
                send_copy = st.checkbox(
                    "📋 M'envoyer une copie",
                    help="Recevez une copie du rapport"
                )
            
            # Sujet par défaut selon le type d'analyse
            analysis_type = str(analysis_results.get('type', 'single')).lower()
            subject_key = f"subject_{analysis_type}"
            default_subject = EmailConfig.EMAIL_TEMPLATES.get(
                subject_key, EmailConfig.EMAIL_TEMPLATES['subject_single']
            )
            subject_input = st.text_input(
                "📝 Sujet",
                value=default_subject,
                help="Modifiez le sujet de l'email si nécessaire"
            )

            custom_message = st.text_area(
                "💬 Message personnalisé (optionnel)",
                placeholder="Ajoutez un message personnel...",
                height=100
            )
            
            if attachments:
                st.markdown("#### 📎 Pièces jointes")
                total_size = sum(Path(f).stat().st_size for f in attachments) / (1024 * 1024)
                for attachment in attachments:
                    filename = Path(attachment).name
                    size_mb = Path(attachment).stat().st_size / (1024 * 1024)
                    st.markdown(f"📄 **{filename}** ({size_mb:.1f} MB)")
                st.info(f"📊 Taille totale: {total_size:.1f} MB")
                if total_size > EmailConfig.MAX_ATTACHMENT_SIZE_MB:
                    st.warning(f"⚠️ Les fichiers seront compressés en ZIP (limite: {EmailConfig.MAX_ATTACHMENT_SIZE_MB} MB)")
            
            submitted = st.form_submit_button("📤 Envoyer le Rapport", type="primary")

        if submitted:
            if not self.sender.is_configured():
                st.error("❌ Configuration email manquante (SMTP_EMAIL/SMTP_PASSWORD)")
                return
                if not recipient_email:
                    st.error("❌ Veuillez saisir une adresse email")
                    return
                if not self.sender.validate_email(recipient_email):
                    st.error("❌ Format d'email invalide")
                    return
                with st.spinner("📤 Envoi en cours..."):
                    success, message = self.sender.send_analysis_report(
                        recipient_email=recipient_email,
                        analysis_results=analysis_results,
                        attachments=attachments,
                    custom_message=custom_message,
                    subject_override=subject_input
                    )
                if success:
                    st.success(message)
                    if send_copy and self.sender.smtp_email != recipient_email:
                        copy_success, copy_message = self.sender.send_analysis_report(
                            recipient_email=self.sender.smtp_email,
                            analysis_results=analysis_results,
                            attachments=attachments,
                            custom_message=f"[COPIE] {custom_message}" if custom_message else "[COPIE]"
                        )
                        if copy_success:
                            st.info(f"📋 Copie envoyée à {self.sender.smtp_email}")
                        else:
                            st.warning(f"⚠️ Impossible d'envoyer la copie: {copy_message}")
                else:
                    st.error(message)


# Fonction d'aide pour l'intégration facile
def create_email_interface() -> EmailInterface:
    """Crée une instance de l'interface email."""
    return EmailInterface()

def quick_send_email(analysis_results: Dict, attachments: Optional[List[str]] = None) -> EmailInterface:
    """
    Interface rapide pour l'envoi d'email.
    
    Returns:
        Instance de EmailInterface configurée
    """
    interface = EmailInterface()
    interface.show_send_email_interface(analysis_results, attachments)
    return interface