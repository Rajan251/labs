import { Router } from 'express';
import { getUploadUrl, completeUpload } from '../controllers/upload.controller';

const router = Router();

router.post('/init', getUploadUrl);
router.post('/:videoId/complete', completeUpload);

export default router;
