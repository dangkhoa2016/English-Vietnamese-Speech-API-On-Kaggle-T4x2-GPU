# Chính sách bảo mật

> 🌐 Language / Ngôn ngữ: [English](SECURITY.md) | **Tiếng Việt**

Không công khai API key, GitHub token, Kaggle credential, model-access credential, Cloudflare tunnel token hoặc dữ liệu giọng nói riêng tư trong issue hay pull request.

Chỉ coordinator boundary được phép public và chỉ khi `API_AUTH_REQUIRED=true`. Hai worker nội bộ ở port 8091 và 8092 không phải public service.

Khi nghi ngờ lỗ hổng, hãy liên hệ riêng maintainer qua `i.am@dangkhoa.dev`, kèm cách tái lập và revision bị ảnh hưởng. Tránh công bố exploit trước khi có bản sửa.
